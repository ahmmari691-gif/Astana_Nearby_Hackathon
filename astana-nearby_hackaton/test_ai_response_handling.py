# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
import app
from test_app import BASE

class AiResponseHandlingTests(unittest.TestCase):
 def test_optional_fields_may_be_omitted(self):
  with patch.object(app,'gemini_json',return_value={'include':['cafe'],'summary':'Кофе'}):p=app.ai_profile('Хочу кофе','ru')
  self.assertEqual(p['food_requirements'],[]);self.assertFalse(p['food_unverified'])
 def test_unknown_categories_still_rejected(self):
  with patch.object(app,'gemini_json',return_value={'include':['invented']}):
   with self.assertRaises(ValueError):app.ai_profile('Хочу кофе','ru')
 def test_fenced_json_is_readable(self):
  response={'choices':[{'message':{'content':'```json\n{"include":["cafe"]}\n```'},'finish_reason':'stop'}]}
  with patch.object(app,'gemini_complete',return_value=response):result=app.gemini_json({})
  self.assertEqual(result['include'],['cafe'])
 def test_truncated_response_is_not_silently_used(self):
  response={'choices':[{'message':{'content':'{}'},'finish_reason':'length'}]}
  with patch.object(app,'gemini_complete',return_value=response):
   with self.assertRaisesRegex(ValueError,'Truncated'):app.gemini_json({})
 def test_specific_reason_is_returned_without_raw_error(self):
  with patch.object(app,'KEY','fake'),patch.object(app,'DIGIS_KEY',''),patch.object(app,'ai_profile',side_effect=RuntimeError('лимит Gemini fake-secret')),patch.object(app,'dataset',return_value={'places':[]}):
   result=app.recommend(dict(BASE,use_ai=True))
  self.assertEqual(result['understanding_error'],'aiQuota');self.assertNotIn('fake-secret',str(result))
 def test_timeout_has_separate_reason(self):self.assertEqual(app.ai_failure_reason(TimeoutError()),'aiTimeout')

if __name__=='__main__':unittest.main()
