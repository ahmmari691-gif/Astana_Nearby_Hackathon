# -*- coding: utf-8 -*-
import copy,datetime,json,pathlib,tempfile,unittest
from unittest.mock import patch
import app,catalog,collect_2gis,sources
from test_app import BASE,place

def raw(**changes):
    value={'id':'123456','name':'Test sushi','name_ex':{'primary':'Test sushi','extension':'ресторан'},
           'point':{'lat':51.1282,'lon':71.4304},'rubrics':[{'name':'Рестораны'}],
           'attribute_groups':[{'attributes':[{'name':'Суши'}]}],
           'schedule':{'Mon':{'working_hours':[{'from':'09:00','to':'22:00'}]}},
           'reviews':{'general_rating':4.7,'general_review_count':20}}
    value.update(changes);return value

def normalized(**changes):
    return sources.normalize_2gis_item(raw(**changes),datetime.datetime.now(datetime.timezone.utc).isoformat())

class VerificationTests(unittest.TestCase):
    def setUp(self):
        mock=patch('request_dataset.save_batch');mock.start();self.addCleanup(mock.stop)
    def test_deleted_and_closed_filtered(self):
        for fields in ({'is_deleted':True},{'dates':{'deleted_at':'2026-01-01'}},
                       {'flags':{'temporary_closed':'true'}},{'flags':{'permanently_closed':True}}):
            self.assertIsNone(normalized(**fields))
    def test_absent_closure_is_not_claim_of_open_now(self):
        p=normalized();self.assertTrue(sources.listed_recently(p))
        self.assertEqual(p['verification']['status'],'listed')
    def test_schedule_and_rating_are_provider_fields(self):
        p=normalized();self.assertIn('09:00',p['hours']);self.assertEqual(p['external_sources'][0]['rating'],4.7)
    def test_negated_sushi_does_not_prove_menu(self):
        for text in ('Нет суши','Без суши','Суши нет'):
            p=normalized(attribute_groups=[{'attributes':[{'name':text}]}])
            self.assertFalse(p['external_sources'][0]['facts'])
    def test_expired_or_future_source_rejected(self):
        for days in (-1,1):
            p=normalized();p['verification']['checked_at']=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=days)).isoformat()
            self.assertFalse(sources.listed_recently(p))
    def test_external_sources_retained(self):
        self.assertEqual(sources.enrich_places([normalized()])[0]['external_sources'][0]['provider'],'2ГИС')
    def test_without_key_no_stale_fallback(self):
        with patch.object(app,'DIGIS_KEY',''),patch.object(app,'dataset',return_value={'places':[place(kind='restaurant',food_tags={'cuisine':'sushi'})]}):
            self.assertEqual(app.recommend(dict(BASE,query='Хочу суши'))['items'],[])
    def test_api_is_mandatory_even_without_web_checkbox(self):
        with patch.object(app,'DIGIS_KEY','fake'),patch.object(app,'dataset',return_value={'places':[]}),patch.object(app,'search_2gis',return_value=[normalized()]) as request:
            result=app.recommend(dict(BASE,query='Хочу суши',web_search=False))
            self.assertEqual(len(result['items']),1);request.assert_called_once()
    def test_fresh_record_without_sushi_rejects_old_menu(self):
        old=place(kind='restaurant',food_tags={'cuisine':'sushi'})
        with patch.object(app,'DIGIS_KEY','fake'),patch.object(app,'dataset',return_value={'places':[old]}),patch.object(app,'search_2gis',return_value=[]),patch.object(app,'verify_2gis_place',return_value=normalized(attribute_groups=[])):
            self.assertEqual(app.recommend(dict(BASE,query='Хочу суши'))['items'],[])
    def test_collection_deduplicates_and_records_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory);(root/'data').mkdir()
            response={'meta':{'code':200},'result':{'items':[raw(),raw(),raw(id='234567',is_deleted=True)],'total':3}}
            actual_build=catalog.build
            with patch.object(collect_2gis,'ROOT',root),patch.object(collect_2gis,'QUERIES',('кафе',)),patch.object(collect_2gis,'provider_json',return_value=response),patch.object(collect_2gis,'build',side_effect=lambda rows,meta:actual_build(rows,meta,root/'data/catalog.sqlite')):
                result=collect_2gis.collect('fake-secret',1)
            self.assertEqual(result['count'],1);self.assertEqual(result['source'],'2ГИС');self.assertFalse(result['complete_city'])
            self.assertNotIn('fake-secret',(root/'data/2gis-collected.json').read_text())
    def test_provider_error_does_not_create_dataset(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(collect_2gis,'ROOT',pathlib.Path(directory)),patch.object(collect_2gis,'provider_json',return_value={'meta':{'code':403}}):
            with self.assertRaises(ValueError):collect_2gis.collect('fake',1)
            self.assertFalse((pathlib.Path(directory)/'data/catalog.sqlite').exists())

if __name__=='__main__':unittest.main()
