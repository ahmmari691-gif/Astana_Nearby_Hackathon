# -*- coding: utf-8 -*-
import json,unittest,urllib.error
from unittest.mock import patch
import app

class GeminiProviderTests(unittest.TestCase):
 def setUp(self):
  mock=patch.object(app,'list_gemini_models',return_value={'gemini-3.5-flash-lite'});mock.start();self.addCleanup(mock.stop)
  selected=patch.object(app,'GEMINI_SELECTED','');selected.start();self.addCleanup(selected.stop)
 def test_request_goes_to_google_with_terminal_key(self):
  class Response:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self):return b'{"choices":[{"message":{"content":"OK"}}]}'
  with patch.object(app.urllib.request,'urlopen',return_value=Response()) as request:
   app.verify_gemini_key('fake-terminal-key')
  req=request.call_args[0][0]
  self.assertEqual(req.full_url,'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions')
  self.assertEqual(req.get_header('Authorization'),'Bearer fake-terminal-key')
  self.assertEqual(json.loads(req.data)['model'],'gemini-3.5-flash-lite')
 def test_quota_error_does_not_reveal_key(self):
  error=urllib.error.HTTPError('https://example.invalid',429,'quota',{},None)
  with patch.object(app.urllib.request,'urlopen',side_effect=error):
   with self.assertRaisesRegex(RuntimeError,'лимит Gemini') as result:
    app.verify_gemini_key('fake-secret')
  self.assertNotIn('fake-secret',str(result.exception))
 def test_empty_completion_not_accepted_as_working_key(self):
  with patch.object(app,'gemini_complete',return_value={}):
   with self.assertRaises(RuntimeError):app.verify_gemini_key('fake')

class GeminiDiagnosticsTests(unittest.TestCase):
 def test_raw_error_is_never_displayed(self):
  body='{"error":{"message":"API key not valid: fake-secret"}}'
  result=app.gemini_error(400,body)
  self.assertIn('ключ отклонён',result);self.assertNotIn('fake-secret',result)
 def test_zero_quota_has_distinct_explanation(self):
  self.assertIn('равна нулю',app.gemini_error(429,'quota exceeded, limit: 0'))
 def test_region_has_distinct_explanation(self):
  self.assertIn('региона',app.gemini_error(400,'User location is not supported'))
 def test_missing_model_has_distinct_explanation(self):
  self.assertIn('модель недоступна',app.gemini_error(404))

class ModelSelectionTests(unittest.TestCase):
 def test_404_tries_next_available_model(self):
  with patch.object(app,'GEMINI_SELECTED',''),patch.object(app,'list_gemini_models',return_value={'gemini-3.5-flash-lite','gemini-3.1-flash-lite'}),patch.object(app,'gemini_complete',side_effect=[RuntimeError('Gemini: выбранная модель недоступна.'),{'choices':[{}]}]) as complete:
   app.verify_gemini_key('fake')
   self.assertEqual(app.GEMINI_SELECTED,'gemini-3.1-flash-lite');self.assertEqual(complete.call_count,2)
 def test_quota_error_is_not_hidden_by_model_switch(self):
  with patch.object(app,'GEMINI_SELECTED',''),patch.object(app,'list_gemini_models',return_value={'gemini-3.5-flash-lite','gemini-3.1-flash-lite'}),patch.object(app,'gemini_complete',side_effect=RuntimeError('лимит Gemini')) as complete:
   with self.assertRaisesRegex(RuntimeError,'лимит Gemini'):app.verify_gemini_key('fake')
   self.assertEqual(complete.call_count,1)

if __name__=='__main__':unittest.main()
