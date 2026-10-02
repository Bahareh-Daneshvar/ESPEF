"""Stream cached pages into yearly Parquets, audits and a master manifest."""
import collections, datetime, gzip, hashlib, json, os, pathlib, re, sqlite3, unicodedata
import pyarrow as pa
import pyarrow.parquet as pq
from reconstruct_abstracts import reconstruct, unusable_reason
RAW_FIELDS=['id','doi','title','abstract_inverted_index','publication_date','publication_year','type','language','primary_topic','topics','primary_location','locations','created_date','updated_date']
RAW_SCHEMA=pa.schema([(k,pa.int64() if k=='publication_year' else pa.string()) for k in RAW_FIELDS])
MODEL_SCHEMA=pa.schema([(k,pa.string()) for k in ['openalex_id','doi','title','abstract','publication_date','type','language','primary_topic_id','primary_topic_name','primary_source_id','primary_source_name','quality_flags']]+[('publication_year',pa.int64()),('abstract_word_count',pa.int64())])
def atomic(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2));os.replace(temp,path)
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def policy_sha(config):return hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
def verify_completed(root,config,year):
    p=root/'data/audits'/f'espef_audit_{year}.json'
    if not p.exists():return False
    a=json.loads(p.read_text())
    if not a.get('validation_passed'):return False
    if a['configuration_sha256']!=policy_sha(config):raise RuntimeError(f'{year}: configuration differs from completed year')
    paths=[root/item['path'] for item in a['files'].values()]
    # A fresh Git clone has audit metadata but deliberately no full Parquets.
    if paths and not any(path.exists() for path in paths):return False
    for item in a['files'].values():
        path=root/item['path']
        if not path.exists() or sha(path)!=item['sha256']:raise RuntimeError(f'{year}: completed-file checksum mismatch')
    return True

def quarter(date):return f'{date[:4]}Q{(int(date[5:7])-1)//3+1}'
def source(w):
    s=(w.get('primary_location') or {}).get('source') or {}
    return s.get('id') or 'MISSING',s.get('display_name') or 'MISSING'
def suspected_text_language(title,text):
    letters=[c for c in title+' '+(text or '') if c.isalpha()]
    return len(letters)>=20 and sum(c.isascii() for c in letters)/len(letters)<0.5

def finalize_year(root,config,year):
    start,end=config['years'][str(year)];folder=root/'data/checkpoints'/str(year)
    states=[json.loads(p.read_text()) for p in sorted(folder.glob('Q*/state.json'))]
    expected_quarters=3 if year==2026 else 4
    if len(states)!=expected_quarters or not all(s['complete'] for s in states):raise RuntimeError('Year is not cursor-complete')
    for s in states:
        if s['retrieved']!=s['initial_count']:raise RuntimeError('Cursor count reconciliation failed')
    rawpath=root/'data/raw'/f'openalex_espef_{year}.parquet';modelpath=root/'data/processed'/f'espef_corpus_{year}.parquet'
    for p in [rawpath,modelpath]:p.parent.mkdir(parents=True,exist_ok=True)
    rawtemp=rawpath.with_suffix('.parquet.tmp');modeltemp=modelpath.with_suffix('.parquet.tmp')
    dbpath=folder/'validation_index.sqlite'
    if dbpath.exists():dbpath.unlink()
    db=sqlite3.connect(':memory:');db.execute('CREATE TABLE seen (id TEXT PRIMARY KEY, doi TEXT, title TEXT)')
    n=0;used=0;exclusion=collections.Counter();flags=collections.Counter();typesraw=collections.Counter();typesclean=collections.Counter();sourcesraw=collections.Counter();sourcesclean=collections.Counter();quartersraw=collections.Counter();quartersclean=collections.Counter();jraw=0;jclean=0;ab_lengths=collections.Counter();badrecords=[];duplicatesid=0
    with pq.ParquetWriter(rawtemp,RAW_SCHEMA,compression=config['compression']) as rw,pq.ParquetWriter(modeltemp,MODEL_SCHEMA,compression=config['compression']) as mw:
        rb=[];mb=[]
        for qfolder in sorted(folder.glob('Q*')):
            state=json.loads((qfolder/'state.json').read_text())
            pages=sorted(qfolder.glob('page_*.json.gz'))
            if len(pages)!=state['pages']:raise RuntimeError('Missing or excess cached pages')
            previous='*'
            for pagefile in pages:
                with gzip.open(pagefile,'rt',encoding='utf-8') as f: page=json.load(f)
                if page['input_cursor']!=previous or page['query_fingerprint']!=state['query_fingerprint']:raise RuntimeError('Cached cursor chain invalid')
                payload=page['response'];previous=payload['meta'].get('next_cursor')
                for w in payload['results']:
                    n+=1;date=w.get('publication_date');text,reason=reconstruct(w.get('abstract_inverted_index'))
                    rb.append({k:json.dumps(w.get(k),ensure_ascii=False,separators=(',',':')) if isinstance(w.get(k),(dict,list)) else w.get(k) for k in RAW_FIELDS})
                    typesraw[w.get('type')]+=1;sourcesraw[source(w)]+=1
                    try:
                        datetime.date.fromisoformat(date)
                        if not start<=date<=end:raise ValueError()
                        q=quarter(date);quartersraw[q]+=1;jraw+=date.endswith('-01-01')
                    except (TypeError,ValueError):reason='missing_or_invalid_publication_date';q='INVALID'
                    if not isinstance(w.get('title'),str) or not w['title'].strip():reason='missing_or_empty_title'
                    if w.get('language')!=config['language']:reason='metadata_language_mismatch'
                    if w.get('type') not in config['work_types']:reason='work_type_mismatch'
                    topic=w.get('primary_topic') or {};subfield=topic.get('subfield') or {}
                    if str(subfield.get('id','')).split('/')[-1]!=config['primary_subfield_id']:reason='primary_subfield_mismatch'
                    if reason is None:reason=unusable_reason(text,config['quality_policy'])
                    doi=(w.get('doi') or '').strip().casefold() or None
                    normalized=unicodedata.normalize('NFKC',re.sub(r'\W+',' ',(w.get('title') or '').casefold())).strip()
                    try:db.execute('INSERT INTO seen VALUES (?,?,?)',(w['id'],doi,normalized))
                    except sqlite3.IntegrityError:duplicatesid+=1;reason='duplicate_openalex_id'
                    qflags=[]
                    if date and date.endswith('-01-01'):qflags.append('january_1_date_precision_unverified')
                    if text and len(text.split())<20:qflags.append('short_abstract_review')
                    if suspected_text_language(w.get('title') or '',text):qflags.append('suspected_text_language_mismatch_review')
                    if year==2026:qflags.append('coverage_pending_stage_1B')
                    if any('arxiv' in json.dumps(l).casefold() for l in w.get('locations',[])) and (w.get('primary_location') or {}).get('is_published'):qflags.append('preprint_published_date_review')
                    for flag in qflags:flags[flag]+=1
                    if reason:
                        exclusion[reason]+=1
                        badrecords.append({'openalex_id':w.get('id'),'reason':reason,'publication_date':date})
                    else:
                        used+=1;typesclean[w['type']]+=1;sourcesclean[source(w)]+=1;quartersclean[q]+=1;jclean+=date.endswith('-01-01');ab_lengths[len(text.split())]+=1
                        sid,sname=source(w)
                        mb.append({'openalex_id':w['id'],'doi':w.get('doi'),'title':w['title'],'abstract':text,'publication_date':date,'publication_year':w.get('publication_year'),'type':w['type'],'language':w['language'],'primary_topic_id':topic.get('id'),'primary_topic_name':topic.get('display_name'),'primary_source_id':None if sid=='MISSING' else sid,'primary_source_name':None if sname=='MISSING' else sname,'quality_flags':json.dumps(qflags),'abstract_word_count':len(text.split())})
                    if len(rb)>=2000:rw.write_table(pa.Table.from_pylist(rb,schema=RAW_SCHEMA));rb=[]
                    if len(mb)>=2000:mw.write_table(pa.Table.from_pylist(mb,schema=MODEL_SCHEMA));mb=[]
                db.commit()
            if previous is not None and payload['results']:raise RuntimeError('Terminal cursor not reached')
        if rb:rw.write_table(pa.Table.from_pylist(rb,schema=RAW_SCHEMA))
        if mb:mw.write_table(pa.Table.from_pylist(mb,schema=MODEL_SCHEMA))
    expected=sum(s['initial_count'] for s in states)
    if n!=expected or used+sum(exclusion.values())!=n:raise RuntimeError('Year totals do not reconcile')
    if pq.ParquetFile(rawtemp).metadata.num_rows!=n or pq.ParquetFile(modeltemp).metadata.num_rows!=used:raise RuntimeError('Parquet row-count validation failed')
    def repeats(column):
        return [{'value':value,'count':count} for value,count in db.execute(f'SELECT {column}, COUNT(*) FROM seen WHERE {column} IS NOT NULL AND {column} != ? GROUP BY {column} HAVING COUNT(*)>1',('',))]
    doi_dups=repeats('doi');title_dups=repeats('title')
    # Keep the lightweight ID/DOI/title index in memory until atomic final backup.
    # This avoids long-lived writable SQLite journals on replicated workspaces.
    checkdb=db
    cross=[]
    for prior in sorted(root.glob('data/checkpoints/*/validation_index.sqlite')):
        if prior==dbpath:continue
        py=int(prior.parent.name)
        if py>=year or not verify_completed(root,config,py):continue
        checkdb.execute('ATTACH DATABASE ? AS prior',(str(prior),))
        cross.extend({'id':row[0],'prior_year':py} for row in checkdb.execute('SELECT current_work.id FROM main.seen AS current_work INNER JOIN prior.seen AS prior_work ON current_work.id=prior_work.id'))
        checkdb.execute('DETACH DATABASE prior')
    if cross:raise RuntimeError('Cross-year OpenAlex ID overlap found; dates may have changed during extraction')
    index_temp=dbpath.with_suffix('.sqlite.tmp')
    if index_temp.exists():index_temp.unlink()
    with sqlite3.connect(index_temp) as output_db:db.backup(output_db)
    db.close()
    os.replace(index_temp,dbpath)
    os.replace(rawtemp,rawpath);os.replace(modeltemp,modelpath)
    files={kind:{'path':str(path.relative_to(root)),'size_bytes':path.stat().st_size,'sha256':sha(path),'rows':n if kind=='raw' else used} for kind,path in [('raw',rawpath),('processed',modelpath)]}
    def sourcedict(counter):return [{'source_id':key[0],'source_name':key[1],'count':count} for key,count in counter.most_common()]
    # Integer language metadata mismatches and text flags remain separate.
    audit={'year':year,'start_date':start,'end_date':end,'extraction_started_at':min(s['started_at'] for s in states),'validated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'configuration_sha256':policy_sha(config),'year_filter':states[0]['params']['filter'].replace(states[0]['params']['filter'].split('from_publication_date:')[1].split(',')[0],start).replace(states[0]['params']['filter'].split('to_publication_date:')[1].split(',')[0],end),'quarter_queries':[s['params'] for s in states],'total_retrieved_works':n,'usable_works':used,'usable_definition':'passes frozen deterministic structural/placeholder rules; semantic and historical QC flags require review before modelling','exclusions':dict(exclusion),'missing_invalid_abstracts':{k:v for k,v in exclusion.items() if 'abstract' in k},'metadata_language_mismatches':exclusion['metadata_language_mismatch'],'suspected_text_language_mismatches':flags['suspected_text_language_mismatch_review'],'quality_flags':dict(flags),'duplicate_indicators':{'openalex_id_removed':duplicatesid,'doi_groups':doi_dups,'normalized_title_groups':title_dups,'cross_year_id_overlaps':cross,'possible_version_pairs':'flagged through locations; DOI/title groups are not blindly deleted'},'work_types_raw':dict(typesraw),'work_types_processed':dict(typesclean),'sources_raw':sourcedict(sourcesraw),'sources_processed':sourcedict(sourcesclean),'quarterly_raw':dict(quartersraw),'quarterly_processed':dict(quartersclean),'january_1':{'raw_count':jraw,'raw_pct':100*jraw/n if n else 0,'processed_count':jclean,'processed_pct':100*jclean/used if used else 0,'precision':'not presumed exact; dates preserved unchanged'},'abstract_length_histogram':dict(ab_lengths),'files':files,'validation_passed':True,'modelling_approved':False,'coverage_status':'pending_stage_1B' if year==2026 else 'coverage_and_date_QC_flags_require_review'}
    atomic(root/'data/audits'/f'espef_audit_{year}.json',audit)
    atomic(root/'data/audits'/f'espef_exclusions_{year}.json',badrecords)
    import csv
    with (root/'data/audits'/f'espef_quarterly_{year}.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['quarter','total_retrieved','usable_works'])
        for q in sorted(quartersraw):writer.writerow([q,quartersraw[q],quartersclean[q]])
    return audit

def write_master(root,config,blocked_reason=None):
    entries={}
    for y,bounds in config['years'].items():
        p=root/'data/audits'/f'espef_audit_{y}.json'
        if p.exists():
            a=json.loads(p.read_text());entries[y]={'status':'validated','date_range':bounds,'initial_matching_count':a['total_retrieved_works'],'retrieved':a['total_retrieved_works'],'usable':a['usable_works'],'files':a['files'],'audit_path':str(p.relative_to(root)),'audit_sha256':sha(p),'coverage_status':a['coverage_status'],'modelling_approved':False}
        else:
            checkpoints=[]
            for s in sorted((root/'data/checkpoints'/y).glob('Q*/state.json')):
                st=json.loads(s.read_text());checkpoints.append({'quarter':s.parent.name,'initial_matching_count':st.get('initial_count'),'retrieved':st['retrieved'],'pages':st['pages'],'complete':st['complete'],'path':str(s.relative_to(root))})
            entries[y]={'status':'checkpointed_incomplete' if checkpoints else 'not_started','date_range':bounds,'initial_matching_count':sum(s['initial_matching_count'] for s in checkpoints) if checkpoints and all(s['initial_matching_count'] is not None for s in checkpoints) else None,'retrieved':sum(s['retrieved'] for s in checkpoints),'checkpoints':checkpoints,'coverage_status':'pending_stage_1B' if y=='2026' else 'not_audited','modelling_approved':False}
    manifest={'project':'ESPEF','storage':'year-partitioned Parquet only; no monolithic corpus','endpoint':config['endpoint'],'corpus':config['corpus'],'primary_subfield_id':config['primary_subfield_id'],'language':config['language'],'work_types':config['work_types'],'citation_filter':None,'configuration_sha256':policy_sha(config),'quality_policy':config['quality_policy'],'abstract_reconstruction':'unique nonnegative integer positions; contiguous from zero; join in position order','publication_date_definition':'OpenAlex publication_date unchanged; annual storage does not redefine temporal chunks','years':entries,'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'blocked_reason':blocked_reason,'all_years_validated':all(x['status']=='validated' for x in entries.values()),'modelling_approved':False,'completeness_2026':'pending_stage_1B','credentials':'environment only; never embedded'}
    atomic(root/'data/espef_dataset_manifest.json',manifest)
