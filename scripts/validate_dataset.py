import argparse,json,pathlib
from audit_dataset import verify_completed
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--year',required=True,type=int);a=p.parse_args()
c=json.loads((ROOT/'config/openalex.json').read_text())
if not verify_completed(ROOT,c,a.year):raise SystemExit('Year not complete: do not treat partial cached pages as a corpus')
print(f'{a.year}: completed audit, config fingerprint, Parquet existence and SHA-256 verified')
