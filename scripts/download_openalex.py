"""Cursor-paginated extraction. Years run sequentially; quarter cursors stay within a year.
No automatic background scheduling, API key acquisition, modelling, or GitHub upload.
"""
import argparse, concurrent.futures, datetime, gzip, hashlib, json, os, pathlib, threading, time
import requests
from audit_dataset import finalize_year, verify_completed, write_master
ROOT = pathlib.Path(__file__).resolve().parents[1]

def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    os.replace(temp, path)

def quarter_windows(start, end):
    a = datetime.date.fromisoformat(start); b = datetime.date.fromisoformat(end)
    for quarter in range(1, 5):
        left = datetime.date(a.year, 3*quarter-2, 1)
        right = (datetime.date(a.year+1, 1, 1) if quarter == 4 else datetime.date(a.year, 3*quarter+1, 1)) - datetime.timedelta(days=1)
        left, right = max(a, left), min(b, right)
        if left <= right:
            yield quarter, str(left), str(right)

def filter_for(config, start, end):
    return f"primary_topic.subfield.id:{config['primary_subfield_id']},from_publication_date:{start},to_publication_date:{end},language:{config['language']},type:{'|'.join(config['work_types'])}"

class Download:
    def __init__(self, config, limit):
        self.config = config; self.limit = limit; self.calls = 0; self.lock = threading.Lock(); self.stop = threading.Event()
    def get(self, session, params):
        for attempt in range(self.config['max_retries']):
            if self.stop.is_set():
                raise RuntimeError('Extraction paused by another worker; checkpoint retained')
            with self.lock:
                if self.calls >= self.limit:
                    self.stop.set(); raise RuntimeError('Configured request budget reached; checkpoint retained')
                self.calls += 1
            request_params = dict(params)
            key = os.environ.get('OPENALEX_API_KEY')
            if key: request_params['api_key'] = key
            try:
                response = session.get(self.config['endpoint'], params=request_params, timeout=(15, 60))
            except requests.RequestException:
                if attempt + 1 == self.config['max_retries']:
                    self.stop.set(); raise RuntimeError('Network retries exhausted; checkpoint retained') from None
                time.sleep(min(2**attempt, 30)); continue
            if response.status_code in (401, 403):
                self.stop.set(); raise RuntimeError(f'OpenAlex access blocked (HTTP {response.status_code}); no credentials logged')
            if response.status_code == 429:
                # Avoid repeatedly spending requests on a daily-budget limit.
                self.stop.set(); raise RuntimeError('OpenAlex rate or daily usage limit (HTTP 429); checkpoint retained')
            if response.status_code >= 500:
                if attempt + 1 == self.config['max_retries']:
                    self.stop.set(); raise RuntimeError('OpenAlex server retries exhausted')
                time.sleep(min(2**attempt, 30)); continue
            if response.status_code != 200:
                self.stop.set(); raise RuntimeError(f'OpenAlex request failed (HTTP {response.status_code}); query unchanged')
            return response.json()
        raise RuntimeError('Request failed')
    def quarter(self, year, quarter, start, end):
        config = self.config
        params = {'filter': filter_for(config,start,end), 'corpus':config['corpus'], 'per_page':config['per_page'], 'select':','.join(config['fields']), 'sort':'publication_date:asc'}
        fingerprint = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
        folder = ROOT/'data/checkpoints'/str(year)/f'Q{quarter}'
        folder.mkdir(parents=True, exist_ok=True)
        state_path = folder/'state.json'
        if state_path.exists():
            state = json.loads(state_path.read_text())
            if state['query_fingerprint'] != fingerprint:
                raise RuntimeError('Configuration changed; refusing to mix cached query results')
        else:
            state = {'query_fingerprint':fingerprint,'params':params,'cursor':'*','pages':0,'retrieved':0,'complete':False,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
            atomic_json(state_path,state)
        if state['complete']:
            print(f'{year} Q{quarter}: cached complete ({state["retrieved"]:,})',flush=True); return
        with requests.Session() as session:
            while not state['complete']:
                cursor = state['cursor']; page_number = state['pages']
                page_path = folder/f'page_{page_number:06d}.json.gz'
                if page_path.exists():
                    # Recovery after page commit but before cursor checkpoint: reuse bytes.
                    with gzip.open(page_path,'rt',encoding='utf-8') as f: page=json.load(f)
                    if page['input_cursor'] != cursor or page['query_fingerprint'] != fingerprint:
                        raise RuntimeError('Cached page does not match cursor/query')
                else:
                    payload=self.get(session,{**params,'cursor':cursor})
                    page={'input_cursor':cursor,'query_fingerprint':fingerprint,'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'response':payload}
                    temp=page_path.with_suffix('.tmp')
                    with gzip.open(temp,'wt',encoding='utf-8') as f: json.dump(page,f,ensure_ascii=False,separators=(',',':'))
                    os.replace(temp,page_path)
                payload=page['response']; next_cursor=payload['meta'].get('next_cursor')
                if next_cursor == cursor and payload['results']:
                    raise RuntimeError('Repeated cursor; refusing duplicate page loop')
                state['initial_count']=state.get('initial_count',payload['meta']['count'])
                state['latest_count']=payload['meta']['count']
                state['retrieved']+=len(payload['results']);state['pages']+=1
                state['cursor']=next_cursor
                state['complete']=not payload['results'] or next_cursor is None
                state['last_page_sha256']=hashlib.sha256(page_path.read_bytes()).hexdigest()
                atomic_json(state_path,state)
                if state['pages']%20==0 or state['complete']:
                    print(f'{year} Q{quarter}: {state["retrieved"]:,}/{state["initial_count"]:,} ({state["pages"]} pages)',flush=True)
        if state['retrieved'] != state['initial_count']:
            raise RuntimeError(f'{year} Q{quarter} count changed or retrieval incomplete; validation required before next year')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--years',nargs='+',type=int);parser.add_argument('--request-budget',type=int)
    args=parser.parse_args();config=json.loads((ROOT/'config/openalex.json').read_text())
    years=args.years or [int(y) for y in config['years']]
    if years != sorted(set(years)) or any(str(y) not in config['years'] for y in years):parser.error('Use increasing, unique configured years')
    d=Download(config,args.request_budget or config['max_requests_per_run'])
    write_master(ROOT,config)
    try:
        for year in years:
            if verify_completed(ROOT,config,year):
                print(f'{year}: completed files/checksums verified; skipping download',flush=True);continue
            for prior in (int(y) for y in config['years'] if int(y)<year):
                if not verify_completed(ROOT,config,prior):
                    raise RuntimeError(f'{prior} must be completed and validated before starting {year}')
            start,end=config['years'][str(year)]
            print(f'Starting {year}: {start} to {end}; no other year runs concurrently',flush=True)
            with concurrent.futures.ThreadPoolExecutor(max_workers=config['quarter_workers']) as pool:
                futures=[pool.submit(d.quarter,year,q,a,b) for q,a,b in quarter_windows(start,end)]
                for future in concurrent.futures.as_completed(futures):future.result()
            audit=finalize_year(ROOT,config,year)
            write_master(ROOT,config)
            print(f'{year} VALIDATED: retrieved={audit["total_retrieved_works"]:,}, usable_by_documented_rules={audit["usable_works"]:,}',flush=True)
    except Exception as e:
        write_master(ROOT,config,blocked_reason=str(e)); print(f'PAUSED: {e}',flush=True);return 2
    return 0
if __name__=='__main__':raise SystemExit(main())
