# -*- coding: utf-8 -*-
import datetime,unittest,urllib.parse
from unittest.mock import patch
import app,sources
from understanding import local_profile,clean_profile
from test_app import BASE,place
from test_verification import normalized

class EntertainmentTests(unittest.TestCase):
 def test_categories_supported_by_parser_and_model_schema(self):
  for query,kind in [('Хочу в кино','cinema'),('Хочу в ночной клуб','nightclub'),('Хочу караоке','karaoke'),('Хочу боулинг','bowling')]:
   p=local_profile(query);self.assertEqual(p['include'],[kind]);self.assertFalse(p['unsupported']);clean_profile(p)
 def test_broad_night_request_includes_entertainment(self):
  self.assertEqual(set(local_profile('Ищу необычную ночную активность')['include']),{'cinema','nightclub','karaoke','bowling'})
 def test_provider_categories_are_mapped(self):
  for label,kind in [('Ночные клубы','nightclub'),('Кинотеатры','cinema'),('Караоке','karaoke'),('Боулинг','bowling')]:
   self.assertEqual(normalized(name='Example',name_ex={'primary':'Example','extension':''},rubrics=[{'name':label}])['kind'],kind)
 def test_cinema_plan_does_not_invent_a_screening(self):
  rows,_=app.retrieve(dict(BASE,query='Хочу в кино',minutes=180),[place(kind='cinema'),place('node/2',kind='museum')])
  self.assertEqual(len(rows),1);self.assertIn('не подтверждает сеанс',rows[0]['action'])
 def test_night_club_needs_schedule(self):
  rows,_=app.retrieve(dict(BASE,query='Хочу в ночной клуб',minutes=180),[place(kind='nightclub')])
  self.assertEqual(rows,[])
 def test_searches_alternatives_separately(self):
  sources._PROVIDER_CACHE.clear();queries=[]
  def provider(url):
   queries.append(urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)['q'][0])
   return {'meta':{'code':200},'result':{'items':[]}}
  with patch.object(sources,'provider_json',side_effect=provider):
   sources.search_2gis({'include':['cinema','karaoke']},'fake')
  self.assertEqual(queries,['Астана кинотеатры','Астана караоке']);sources._PROVIDER_CACHE.clear()

if __name__=='__main__':unittest.main()
