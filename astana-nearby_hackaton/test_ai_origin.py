# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
import app
from test_app import BASE
from understanding import local_profile

class AiOriginTests(unittest.TestCase):
 def test_origin_then_map_then_preferences_then_places(self):
  order=[]
  def origin(*args):order.append('origin');return {'name':'Keruen','question':''}
  def mapping(*args):order.append('map');return {'status':'resolved','name':'Keruen','address':'Astana','lat':51.128,'lon':71.43}
  def intent(*args):order.append('preferences');return local_profile('Хочу кафе рядом')
  def places(*args):order.append('places');return []
  data={k:v for k,v in BASE.items() if k not in ('lat','lon')}
  with patch.object(app,'KEY','fake'),patch.object(app,'DIGIS_KEY','fake'),patch.object(app,'ai_start_location',side_effect=origin),patch('text_location.resolve_start',side_effect=mapping) as resolve,patch.object(app,'ai_profile',side_effect=intent),patch.object(app,'search_2gis',side_effect=places),patch.object(app,'dataset',return_value={'places':[]}),patch('request_dataset.save_batch'):
   result=app.recommend(dict(data,query='Я в керуене, хочу кафе рядом',use_ai=True))
  self.assertEqual(order,['origin','map','preferences','places']);self.assertEqual(resolve.call_args[0][0],'Я у Keruen')
  self.assertEqual(result['origin']['understanding_mode'],'semantic')
 def test_unknown_origin_stops_before_preferences(self):
  data={k:v for k,v in BASE.items() if k not in ('lat','lon')}
  with patch.object(app,'KEY','fake'),patch.object(app,'ai_start_location',return_value={'name':None,'question':'Где вы сейчас?'}),patch.object(app,'ai_profile') as preferences:
   result=app.recommend(dict(data,query='Хочу в Мегу',use_ai=True))
  self.assertTrue(result['needs_location']);preferences.assert_not_called()
 def test_ai_does_not_supply_coordinates(self):
  with patch.object(app,'gemini_json',return_value={'origin':'Keruen','lat':1,'lon':2}):result=app.ai_start_location('Я в керуене')
  self.assertNotIn('lat',result);self.assertNotIn('lon',result)
 def test_explicit_coordinates_skip_origin_model(self):
  with patch.object(app,'KEY',''),patch.object(app,'DIGIS_KEY',''),patch.object(app,'ai_start_location') as origin,patch.object(app,'dataset',return_value={'places':[]}):app.recommend(BASE)
  origin.assert_not_called()

if __name__=='__main__':unittest.main()
