# -*- coding: utf-8 -*-
import unittest,urllib.parse
from unittest.mock import patch
import sources,app
from test_verification import raw,normalized
from test_app import BASE

class IndoorSearchTests(unittest.TestCase):
 def setUp(self):sources._PROVIDER_CACHE.clear();sources._MALL_CACHE.clear()
 def tearDown(self):sources._PROVIDER_CACHE.clear();sources._MALL_CACHE.clear()
 def test_tenant_with_mall_in_name_keeps_its_category(self):
  p=normalized(name='Coffee, MEGA Silk Way торговый центр',rubrics=[{'name':'Кофейни'}],name_ex={'primary':'Coffee','extension':'кофейня'})
  self.assertEqual(p['kind'],'cafe')
  p=normalized(name='Cafe',rubrics=[{'name':'Кофейни'}],name_ex={'primary':'Cafe','extension':'кофейня в ТРЦ'})
  self.assertEqual(p['kind'],'cafe')
 def test_building_id_and_floor_are_retained(self):
  p=normalized(address={'building_id':'987654','building_name':'Keruen'},address_comment='3 этаж')
  self.assertEqual(p['building_id'],'987654');self.assertEqual(p['location_comment'],'3 этаж')
 def test_nearby_mall_uses_actual_building_id(self):
  items=[raw(id='111111',name='Keruen',rubrics=[{'name':'Торгово-развлекательные центры'}],name_ex={'primary':'Keruen','extension':'ТРЦ'},address={'building_id':'987654'}),raw(id='222222',name='Far Mall',rubrics=[{'name':'Торговые центры'}],name_ex={'primary':'Far Mall','extension':'ТРЦ'},address={'building_id':'555555'},point={'lat':51.3,'lon':71.7})]
  with patch.object(sources,'provider_json',return_value={'meta':{'code':200},'result':{'items':items}}) as provider:
   malls=sources.nearby_malls(BASE['lat'],BASE['lon'],'fake')
  self.assertEqual(len(malls),1);self.assertEqual(malls[0]['building_id'],'987654')
  query=urllib.parse.parse_qs(urllib.parse.urlsplit(provider.call_args[0][0]).query)
  self.assertNotIn('point',query);self.assertNotIn('lat',query);self.assertNotIn('lon',query)
 def test_indoor_pagination_and_no_duplicates(self):
  mall={'building_id':'987654','name':'Keruen'};calls=[]
  def provider(url):
   params=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query);calls.append(params)
   if 'building_id' not in params:return {'meta':{'code':200},'result':{'items':[raw(id='100010')]}}
   page=int(params['page'][0]);count=5 if page==3 else 10
   items=[raw(id=str(100000+(page-1)*10+i),address={'building_id':'987654'},address_comment='2 этаж') for i in range(count)]
   return {'meta':{'code':200},'result':{'items':items,'total':25}}
  with patch.object(sources,'nearby_malls',return_value=[mall]),patch.object(sources,'provider_json',side_effect=provider):
   rows=sources.search_2gis({'include':['cafe'],'_nearby':{'lat':BASE['lat'],'lon':BASE['lon']}},'fake')
  self.assertEqual(len(rows),25)
  self.assertTrue(all(row['building_name']=='Keruen' for row in rows))
  indoor=[c for c in calls if 'building_id' in c];self.assertEqual(len(indoor),6)
  self.assertTrue(all(c['search_type']==['indoor'] and c['building_id']==['987654'] for c in indoor))
 def test_no_indoor_search_for_walk_in_park(self):
  with patch.object(sources,'nearby_malls') as malls,patch.object(sources,'provider_json',return_value={'meta':{'code':200},'result':{'items':[]}}):
   sources.search_2gis({'include':['park'],'_nearby':{'lat':BASE['lat'],'lon':BASE['lon']}},'fake')
  malls.assert_not_called()
 def test_indoor_does_not_waive_sushi_evidence(self):
  p=normalized(attribute_groups=[],building_name='Mall')
  rows,_=app.retrieve(dict(BASE,query='Хочу суши рядом'),[p]);self.assertEqual(rows,[])
 def test_mall_provider_failure_still_allows_ordinary_search(self):
  with patch.object(sources,'nearby_malls',side_effect=ValueError('unavailable')),patch.object(sources,'provider_json',return_value={'meta':{'code':200},'result':{'items':[raw()]}}):
   rows=sources.search_2gis({'include':['restaurant'],'_nearby':{'lat':BASE['lat'],'lon':BASE['lon']}},'fake')
  self.assertEqual(len(rows),1)

if __name__=='__main__':unittest.main()
