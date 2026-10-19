# -*- coding: utf-8 -*-
import unittest,json
from unittest.mock import patch
import app
from understanding import clean_semantic_profile

class ProfileRepairTests(unittest.TestCase):
 def test_null_optional_fields_and_numeric_strings(self):
  p=clean_semantic_profile({'include':['cafe'],'exclude':None,'food_requirements':None,'indoors':None,'needs_clarification':'false','max_distance_m':'1000','max_minutes':'null'})
  self.assertEqual(p['max_distance_m'],1000);self.assertIsNone(p['max_minutes']);self.assertEqual(p['food_requirements'],[])
 def test_invalid_food_is_never_discarded(self):
  with self.assertRaises(ValueError):clean_semantic_profile({'include':['restaurant'],'food_requirements':'sushi'})
 def test_invalid_category_is_never_discarded(self):
  with self.assertRaises(ValueError):clean_semantic_profile({'include':['invented']})
 def test_zero_model_limits_mean_unspecified(self):
  p=clean_semantic_profile({'include':['cafe'],'max_minutes':0,'max_distance_m':0})
  self.assertIsNone(p['max_minutes']);self.assertIsNone(p['max_distance_m'])
 def test_one_bounded_format_retry(self):
  with patch.object(app,'gemini_json',side_effect=[ValueError('Invalid JSON'),{'include':['cafe'],'max_distance_m':1000}]) as complete:
   p=app.ai_profile('Хочу кофе рядом','ru')
  self.assertEqual(p['include'],['cafe']);self.assertEqual(complete.call_count,2)
 def test_permanent_invalid_response_stops_after_retry(self):
  with patch.object(app,'gemini_json',side_effect=ValueError('Invalid JSON')) as complete:
   with self.assertRaises(ValueError):app.ai_profile('Хочу кофе','ru')
  self.assertEqual(complete.call_count,2)
 def test_quota_failure_is_not_retried(self):
  with patch.object(app,'gemini_json',side_effect=RuntimeError('Достигнут лимит Gemini')) as complete:
   with self.assertRaises(RuntimeError):app.ai_profile('Хочу кофе','ru')
  self.assertEqual(complete.call_count,1)
 def test_food_requirement_survives_retry(self):
  requirement={'type':'dish','value':'sushi'}
  with patch.object(app,'gemini_json',side_effect=[{'include':['restaurant'],'food_requirements':'sushi'},{'include':['restaurant'],'food_requirements':[requirement]}]):
   p=app.ai_profile('Хочу суши','ru')
  self.assertEqual(p['food_requirements'],[requirement])

if __name__=='__main__':unittest.main()
