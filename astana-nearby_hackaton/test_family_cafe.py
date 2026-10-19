# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
import app,sources
from understanding import local_profile,merge_profiles,clean_profile
from test_app import BASE
from test_verification import normalized
QUERY='я хочу сходить в семейное кафе\nУточнение: рядом'

class FamilyCafeTests(unittest.TestCase):
 def test_exact_query(self):
  p=local_profile(QUERY);self.assertEqual(p['include'],['cafe']);self.assertTrue(p['family_dining'])
  self.assertEqual(p['max_distance_m'],1000);self.assertIsNone(p['max_minutes']);self.assertFalse(p['food_unverified'])
 def test_semantic_does_not_erase_family_requirement(self):
  p=merge_profiles(local_profile(QUERY),clean_profile({'include':['park','restaurant']}))
  self.assertTrue(p['family_dining']);self.assertEqual(p['include'],['cafe'])
 def test_only_source_confirmed_family_cafes(self):
  plain=normalized(id='111111',rubrics=[{'name':'Кафе'}],name_ex={'primary':'Обычное','extension':'кафе'})
  family=normalized(id='222222',rubrics=[{'name':'Кафе'}],name_ex={'primary':'Семейное','extension':'семейное кафе'})
  room=normalized(id='333333',rubrics=[{'name':'Кафе'}],name_ex={'primary':'С комнатой','extension':'кафе'},attribute_groups=[{'attributes':[{'name':'Детская комната'}]}])
  fake=normalized(id='444444',rubrics=[{'name':'Кафе'}],name_ex={'primary':'Семейное кафе','extension':'кафе'})
  rows,_=app.retrieve(dict(BASE,query=QUERY),[plain,family,room,fake]);self.assertEqual({p['id'] for p in rows},{'2gis/222222','2gis/333333'})
 def test_negative_room_not_accepted(self):
  p=normalized(rubrics=[{'name':'Кафе'}],name_ex={'primary':'Cafe','extension':'кафе'},attribute_groups=[{'attributes':[{'name':'Нет детской комнаты'}]}])
  self.assertEqual(app.retrieve(dict(BASE,query=QUERY),[p])[0],[])
 def test_radius_remains_one_kilometre(self):
  p=normalized(point={'lat':51.15,'lon':71.4304},rubrics=[{'name':'Кафе'}],name_ex={'primary':'Family','extension':'семейное кафе'})
  self.assertEqual(app.retrieve(dict(BASE,query=QUERY),[p])[0],[])
 def test_family_format_does_not_imply_cuisine(self):
  p=normalized(rubrics=[{'name':'Кафе'}],name_ex={'primary':'Family','extension':'семейное кафе'},attribute_groups=[])
  self.assertEqual(app.retrieve(dict(BASE,query='Хочу семейное кафе с суши рядом'),[p])[0],[])
 def test_search_labels_are_family_specific(self):
  sources._PROVIDER_CACHE.clear()
  with patch.object(sources,'provider_json',return_value={'meta':{'code':200},'result':{'items':[]}}) as request:
   sources.search_2gis(local_profile(QUERY),'fake')
  import urllib.parse
  labels=[urllib.parse.parse_qs(urllib.parse.urlsplit(c.args[0]).query)['q'][0] for c in request.call_args_list]
  self.assertEqual(labels,['Астана Семейные кафе','Астана Семейные рестораны'])

if __name__=='__main__':unittest.main()
