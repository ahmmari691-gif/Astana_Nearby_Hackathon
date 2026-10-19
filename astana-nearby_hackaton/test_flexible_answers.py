# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
import app
from understanding import local_profile,clean_profile,merge_profiles
from test_app import BASE

class FlexibleAnswersTests(unittest.TestCase):
 def test_exact_user_reply_removes_both_limits(self):
  p=local_profile('Хочу музей рядом на 30 минут\nУточнение: у меня много времени и мне не важно где')
  self.assertTrue(p['time_unlimited']);self.assertTrue(p['radius_unlimited'])
  self.assertIsNone(p['max_minutes']);self.assertIsNone(p['max_distance_m'])
 def test_alternative_wordings(self):
  for text in ('Времени много, где угодно','Никуда не спешу, расстояние неважно','Без спешки, по всей Астане'):
   p=local_profile(text);self.assertTrue(p['time_unlimited']);self.assertTrue(p['radius_unlimited'])
 def test_explicit_no_limits_survive_model_hints(self):
  p=merge_profiles(local_profile('Хочу музей, много времени, неважно где'),clean_profile({'include':['museum'],'max_minutes':60,'max_distance_m':1000}))
  self.assertIsNone(p['max_minutes']);self.assertIsNone(p['max_distance_m'])
 def test_does_not_ask_time_or_radius_again(self):
  with patch.object(app,'KEY',''),patch.object(app,'DIGIS_KEY',''),patch.object(app,'dataset',return_value={'places':[]}):
   result=app.recommend(dict(BASE,query='Хочу музей\nУточнение: у меня много времени и мне не важно где'))
  self.assertNotIn('needs_clarification',result);self.assertIsNone(result['filters']['minutes']);self.assertIsNone(result['filters']['radius']);self.assertTrue(result['filters']['radius_unlimited'])

if __name__=='__main__':unittest.main()
