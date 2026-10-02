"""Stream only selected date windows. No embedding or modelling is run here."""
import datetime,json,pathlib
import pyarrow.dataset as ds
ROOT=pathlib.Path(__file__).resolve().parents[1]
def scan_window(start,end,*,allow_unresolved_2026=False,batch_size=1024,columns=None):
    left=datetime.date.fromisoformat(start);right=datetime.date.fromisoformat(end)
    if left>right:raise ValueError('Start is after end')
    manifest=json.loads((ROOT/'data/espef_dataset_manifest.json').read_text())
    if right.year>=2026 and not allow_unresolved_2026:
        raise ValueError('2026 remains pending Stage 1B; explicitly select it for audit only')
    paths=[]
    for y in range(left.year,right.year+1):
        state=manifest['years'].get(str(y),{})
        if state.get('status')!='validated':raise ValueError(f'{y} is not a validated complete partition')
        paths.append(str(ROOT/state['files']['processed']['path']))
    dataset=ds.dataset(paths,format='parquet')
    filt=(ds.field('publication_date')>=start)&(ds.field('publication_date')<=end)
    return dataset.scanner(filter=filt,columns=columns,batch_size=batch_size).to_batches()
