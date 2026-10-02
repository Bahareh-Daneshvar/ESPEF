import copy,gzip,hashlib,json,pathlib,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import download_openalex as downloader
from audit_dataset import finalize_year,verify_completed,write_master
from load_temporal_partition import scan_window
from reconstruct_abstracts import reconstruct
PROJECT=pathlib.Path(__file__).resolve().parents[1]
class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name)
        self.config=json.loads((PROJECT/'config/openalex.json').read_text())
    def tearDown(self):self.tmp.cleanup()
    def fixtures(self,year=2021):
        for q in range(1,5):
            start=f'{year}-{3*q-2:02d}-01';end=f'{year}-{3*q:02d}-28'
            params={'filter':downloader.filter_for(self.config,start,end),'corpus':'core','per_page':200,'select':','.join(self.config['fields']),'sort':'publication_date:asc'}
            fp=hashlib.sha256(json.dumps(params,sort_keys=True).encode()).hexdigest()
            valid={'id':f'W{q}','doi':f'doi:{q}','title':'A valid scientific title '+str(q),'abstract_inverted_index':{'Research':[0],'findings':[1]},'publication_date':start,'publication_year':year,'type':'article','language':'en','primary_topic':{'id':'T1','display_name':'Topic','subfield':{'id':'https://openalex.org/subfields/1702'}},'primary_location':{'source':{'id':'S1','display_name':'Venue'}},'locations':[]}
            invalid=copy.deepcopy(valid);invalid['id']=f'WX{q}';invalid['doi']=None
            if q==1:invalid['abstract_inverted_index']=None
            if q==2:invalid['abstract_inverted_index']={'International':[0],'audience':[1]}
            if q==3:invalid['abstract_inverted_index']={'35.240.67':[0]}
            if q==4:invalid['id']='W1'
            folder=self.root/f'data/checkpoints/{year}/Q{q}';folder.mkdir(parents=True)
            page={'input_cursor':'*','query_fingerprint':fp,'retrieved_at':'2026-10-02T00:00:00Z','response':{'meta':{'count':2,'next_cursor':None},'results':[valid,invalid]}}
            with gzip.open(folder/'page_000000.json.gz','wt') as f:json.dump(page,f)
            state={'query_fingerprint':fp,'params':params,'cursor':None,'pages':1,'retrieved':2,'complete':True,'initial_count':2,'started_at':'2026-10-02T00:00:00Z'}
            (folder/'state.json').write_text(json.dumps(state))
    def test_reconstruction_rejects_collisions_and_gaps(self):
        self.assertEqual(reconstruct({'B':[1],'A':[0]})[0],'A B')
        self.assertIsNotNone(reconstruct({'A':[0],'B':[0]})[1])
        self.assertIsNotNone(reconstruct({'A':[1]})[1])
    def test_finalization_counts_checksums_and_corruption(self):
        self.fixtures();a=finalize_year(self.root,self.config,2021)
        self.assertEqual(a['total_retrieved_works'],8);self.assertEqual(a['usable_works'],4)
        self.assertEqual(a['exclusions']['duplicate_openalex_id'],1)
        self.assertTrue(verify_completed(self.root,self.config,2021))
        write_master(self.root,self.config)
        m=json.loads((self.root/'data/espef_dataset_manifest.json').read_text());self.assertEqual(m['years']['2022']['status'],'not_started')
        p=self.root/a['files']['processed']['path'];p.write_bytes(p.read_bytes()+b'corruption')
        with self.assertRaises(RuntimeError):verify_completed(self.root,self.config,2021)
    def test_cross_year_id_overlap_blocks_finalization(self):
        self.fixtures();finalize_year(self.root,self.config,2021)
        self.fixtures(2022)
        with self.assertRaisesRegex(RuntimeError,'Cross-year OpenAlex ID overlap'):
            finalize_year(self.root,self.config,2022)

    def test_audit_only_clone_can_download_fresh(self):
        self.fixtures();a=finalize_year(self.root,self.config,2021)
        for item in a['files'].values():(self.root/item['path']).unlink()
        self.assertFalse(verify_completed(self.root,self.config,2021))

    def test_orphan_page_reused_after_checkpoint_failure(self):
        self.fixtures();folder=self.root/'data/checkpoints/2021/Q1';s=json.loads((folder/'state.json').read_text())
        s.update(cursor='*',pages=0,retrieved=0,complete=False);(folder/'state.json').write_text(json.dumps(s))
        d=downloader.Download(self.config,1)
        with patch.object(downloader,'ROOT',self.root),patch.object(d,'get',side_effect=AssertionError('Must not download cached page')):
            d.quarter(2021,1,'2021-01-01','2021-03-28')
        s=json.loads((folder/'state.json').read_text());self.assertTrue(s['complete']);self.assertEqual(s['retrieved'],2)
    def test_temporal_loader_rejects_unresolved_2026(self):
        write_master(self.root,self.config)
        import load_temporal_partition as loader
        with patch.object(loader,'ROOT',self.root):
            with self.assertRaises(ValueError):loader.scan_window('2026-01-01','2026-03-31')
if __name__=='__main__':unittest.main()
