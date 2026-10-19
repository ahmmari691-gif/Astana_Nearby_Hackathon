# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
import app
from understanding import local_profile
from test_app import BASE,place

class NearbyAndOriginReplyTests(unittest.TestCase):
 def test_nearby_words_set_existing_radius(self):
  for word in ('ближе','рядом','недалеко'):
   p=local_profile('Хочу кафе '+word);self.assertEqual(p['max_distance_m'],1000)
 def test_explicit_radius_wins_over_vague_nearby_word(self):
  self.assertEqual(local_profile('Хочу кафе рядом, в радиусе 2 км')['max_distance_m'],2000)
 def test_closest_venue_wins_over_name_keyword(self):
  query='Хочу кофе рядом'
  rows,_=app.retrieve(dict(BASE,query=query),[
   place('far',kind='cafe',name='Хочу кофе рядом',lon=71.44),
   place('near',kind='cafe',name='A',lon=71.431),
   place('too-far',kind='cafe',lon=71.46)])
  self.assertEqual(rows[0]['id'],'near');self.assertNotIn('too-far',{p['id'] for p in rows})
 def test_location_reply_resolves_without_changing_user_request(self):
  data={k:v for k,v in BASE.items() if k not in ('lat','lon')}
  data.update(query='Хочу музей',location_hint='Mega Silk Way')
  with patch('text_location.resolve_start',return_value={'status':'missing'}) as resolve:
   result=app.recommend(data)
  self.assertTrue(result['needs_location']);self.assertEqual(resolve.call_args[0][0],'Я у Mega Silk Way')
 def test_form_coordinates_take_priority_over_old_hint(self):
  with patch('text_location.resolve_start') as resolve,patch.object(app,'KEY',''),patch.object(app,'DIGIS_KEY',''),patch.object(app,'dataset',return_value={'places':[]}):
   app.recommend(dict(BASE,location_hint='Old address'))
  resolve.assert_not_called()

if __name__=='__main__':unittest.main()
