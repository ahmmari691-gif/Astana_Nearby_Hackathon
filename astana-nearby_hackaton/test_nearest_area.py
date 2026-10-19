# -*- coding: utf-8 -*-
import unittest,urllib.parse
from unittest.mock import patch
import sources,app
from understanding import local_profile
from test_verification import raw
from test_app import BASE
Q='Я с ребёнком, ищу парк или детскую площадку рядом'
class NearestAreaTests(unittest.TestCase):
 def setUp(self):sources._PROVIDER_CACHE.clear()
 def params(self,call):return urllib.parse.parse_qs(urllib.parse.urlsplit(call.args[0]).query)
 def test_selected_riverfront_sorts_from_public_point(self):
  p=dict(local_profile(Q),_public_anchor={'lat':51.1631,'lon':71.4251})
  with patch.object(sources,'provider_json',return_value={'meta':{'code':200},'result':{'items':[]}}) as request:sources.search_2gis(p,'fake')
  params=self.params(request.call_args);self.assertEqual(params['point'],['71.4251,51.1631']);self.assertEqual(params['sort'],['distance'])
 def test_gps_is_forwarded_to_2gis_for_nearest_search(self):
  p=dict(local_profile(Q),_nearby={'lat':51.163111,'lon':71.425122})
  with patch.object(sources,'nearby_malls',return_value=[]),patch.object(sources,'provider_json',return_value={'meta':{'code':200},'result':{'items':[]}}) as request:sources.search_2gis(p,'fake')
  self.assertTrue(all(self.params(c)['point']==['71.425122,51.163111'] and self.params(c)['sort']==['distance'] for c in request.call_args_list))
 def test_distinct_areas_have_distinct_cache_entries(self):
  with patch.object(sources,'provider_json',return_value={'meta':{'code':200},'result':{'items':[]}}) as request:
   for lat in (51.16,51.12):sources.search_2gis({'include':['park'],'_public_anchor':{'lat':lat,'lon':71.42}},'fake')
  self.assertEqual(request.call_count,2)
 def test_general_search_fetches_next_page(self):
  def provider(url):
   page=int(urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)['page'][0]);count=10 if page==1 else 1
   return {'meta':{'code':200},'result':{'items':[raw(id=str(100000+page*10+i)) for i in range(count)]}}
  with patch.object(sources,'provider_json',side_effect=provider) as request:rows=sources.search_2gis({'include':['park']},'fake')
  self.assertEqual(len(rows),11);self.assertEqual(request.call_count,2)
 def test_selected_radius_is_sent_and_separates_cache(self):
  with patch.object(sources,'nearby_malls',return_value=[]),patch.object(sources,'provider_json',return_value={'meta':{'code':200},'result':{'items':[]}}) as request:
   for radius in (1000,2500):sources.search_2gis({'include':['park'],'_nearby':{'lat':51.16,'lon':71.42},'_search_radius':radius},'fake')
  self.assertEqual([self.params(c)['radius'][0] for c in request.call_args_list],['1000','2500'])
 def test_all_origins_are_passed_for_nearest_search(self):
  for lat,lon,public in [(51.1631,71.4251,True),(51.163111,71.425122,False)]:
   with patch.object(app,'KEY',''),patch.object(app,'DIGIS_KEY','fake'),patch.object(app,'search_2gis',return_value=[]) as search,patch.object(app,'dataset',return_value={'places':[]}),patch.object(app,'verification_gate',return_value=([],'checked')),patch('request_dataset.save_batch'):
    app.recommend(dict(BASE,lat=lat,lon=lon,query=Q))
   self.assertEqual(search.call_args.args[0]['_nearby'],{'lat':lat,'lon':lon})
   self.assertEqual(search.call_args.args[0]['_search_radius'],1000)

if __name__=='__main__':unittest.main()
