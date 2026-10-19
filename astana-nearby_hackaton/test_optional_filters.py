# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
import app
from test_app import BASE
from understanding import local_profile

class OptionalFilterTests(unittest.TestCase):
 def request(self,**values):
  data=dict(BASE);data.pop('minutes');data.pop('radius');data.update(values)
  with patch.object(app,'KEY',''),patch.object(app,'DIGIS_KEY',''),patch.object(app,'dataset',return_value={'places':[]}):return app.recommend(data)
 def test_both_from_text(self):
  result=self.request(query='Хочу музей, у меня 1 час, в радиусе 2,5 км')
  self.assertEqual(result['filters']['minutes'],60);self.assertEqual(result['filters']['radius'],2500)
 def test_neither_provided_asks_only_radius(self):
  result=self.request(query='Хочу музей')
  self.assertEqual(result['missing_fields'],['radius'])
 def test_only_radius_missing(self):
  result=self.request(query='Хочу музей на 30 минут')
  self.assertEqual(result['missing_fields'],['radius'])
 def test_only_time_missing(self):
  result=self.request(query='Хочу музей в пределах 1 км')
  self.assertIsNone(result['filters']['minutes'])
 def test_form_and_text_can_be_combined(self):
  result=self.request(query='Хочу музей в пределах 2 км',minutes=60)
  self.assertEqual(result['filters']['minutes'],60);self.assertEqual(result['filters']['radius'],2000)
 def test_reply_supplies_missing_fields(self):
  result=self.request(query='Хочу музей\nУточнение: у меня час, до 2 км')
  self.assertEqual(result['filters']['minutes'],60);self.assertEqual(result['filters']['radius'],2000)
 def test_missing_fields_do_not_trigger_place_search(self):
  data={k:v for k,v in BASE.items() if k not in ('minutes','radius')}
  with patch.object(app,'KEY',''),patch.object(app,'DIGIS_KEY','fake'),patch.object(app,'search_2gis') as search:
   app.recommend(dict(data,query='Хочу кафе'))
  search.assert_not_called()
 def test_model_can_extract_non_numeric_time(self):
  data={k:v for k,v in BASE.items() if k not in ('minutes','radius')}
  profile=local_profile('Хочу музей');profile.update(max_minutes=90,max_distance_m=1500)
  with patch.object(app,'KEY','fake'),patch.object(app,'DIGIS_KEY',''),patch.object(app,'ai_profile',return_value=profile),patch.object(app,'dataset',return_value={'places':[]}):
   result=app.recommend(dict(data,query='Музей на полтора часа в полутора километрах',use_ai=True))
  self.assertEqual(result['filters']['minutes'],90);self.assertEqual(result['filters']['radius'],1500)

if __name__=='__main__':unittest.main()
