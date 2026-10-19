import json,pathlib,tempfile,unittest
from unittest.mock import patch
import catalog,app,sources
from test_app import place,BASE

class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.db=pathlib.Path(self.directory.name)/'catalog.sqlite'
        catalog.build([place('node/1'),place('node/2',lat=51.30,lon=71.70),place('node/3',kind='restaurant')],{'collected_at':'test'},self.db)
    def tearDown(self):self.directory.cleanup()
    def test_index_returns_nearby_categories_only(self):
        rows=catalog.nearby(51.1282,71.4304,1000,{'park'},self.db)
        self.assertEqual([p['id'] for p in rows],['node/1'])
    def test_summary_does_not_return_place_payloads(self):
        result=catalog.summary(self.db)
        self.assertEqual(result['count'],3);self.assertNotIn('places',result)
    def test_failed_rebuild_keeps_previous_catalog(self):
        def broken():
            yield place('node/4')
            raise ValueError('incomplete import')
        with self.assertRaises(ValueError):catalog.build(broken(),{},self.db)
        self.assertEqual(catalog.summary(self.db)['count'],3)
    def test_nearby_query_uses_spatial_index(self):
        with catalog.connect(self.db) as c:
            plan=c.execute('EXPLAIN QUERY PLAN SELECT p.data FROM spatial r JOIN places p ON p.id=r.id WHERE r.min_lat<? AND r.max_lat>?',(52,50)).fetchall()
        self.assertTrue(any('VIRTUAL TABLE INDEX' in str(row) for row in plan))
    def test_catalog_page_is_bounded_and_pages_do_not_repeat(self):
        rows=[place('node/'+str(i),lon=71.4304+i*0.00001) for i in range(45)]
        with patch.object(catalog,'DB',self.db),patch.object(catalog,'summary',return_value={'source':'2ГИС'}),patch.object(catalog,'nearby',return_value=rows):
            a=app.catalog_page(dict(BASE,query='',offset=0))
            b=app.catalog_page(dict(BASE,query='',offset=20))
        self.assertEqual(len(a['items']),20);self.assertEqual(a['next_offset'],20)
        self.assertFalse({p['id'] for p in a['items']}&{p['id'] for p in b['items']})
    def test_chain_branches_not_collapsed_across_city(self):
        rows,_=app.retrieve(dict(BASE,query='Хочу кофе'),[
            place('node/1',kind='cafe',name='Coffee',lon=71.4304),
            place('node/2',kind='cafe',name='Coffee',lon=71.4354)])
        self.assertEqual(len(rows),2)
    def test_city_boundary_reaches_southern_areas(self):
        app.validate(dict(BASE,lat=50.86,lon=71.6))
    def test_2gis_repeated_query_is_cached(self):
        sources._PROVIDER_CACHE.clear()
        response={'meta':{'code':200},'result':{'items':[]}}
        profile={'food_requirements':[{'type':'cuisine','value':'korean'}]}
        with patch.object(sources,'provider_json',return_value=response) as provider:
            sources.search_2gis(profile,'test-key');sources.search_2gis(profile,'test-key')
            self.assertEqual(provider.call_count,1)
        sources._PROVIDER_CACHE.clear()
    def test_key_validation_errors_do_not_expose_key(self):
        import io
        with patch('urllib.request.urlopen',return_value=io.BytesIO(b'{"meta":{"code":403}}')):
            with self.assertRaises(RuntimeError) as result:
                sources.check_2gis_key('not-a-real-key')
        self.assertNotIn('not-a-real-key',str(result.exception))
        self.assertIn('403',str(result.exception))

if __name__=='__main__':unittest.main()
