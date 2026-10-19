# -*- coding: utf-8 -*-
import io,json,unittest,urllib.error,subprocess
from unittest.mock import patch
import sources
class DigisKeyErrors(unittest.TestCase):
 def test_http_access_error_is_explained_without_secret(self):
  body=json.dumps({'meta':{'code':403,'error':{'message':'Denied for fake-secret-key'}}}).encode()
  error=urllib.error.HTTPError('https://example.test/?key=fake-secret-key',403,'Denied',None,io.BytesIO(body))
  with patch('urllib.request.urlopen',side_effect=error):
   with self.assertRaises(RuntimeError) as got:sources.check_2gis_key('fake-secret-key')
  self.assertIn('403',str(got.exception));self.assertIn('Places API',str(got.exception));self.assertNotIn('fake-secret-key',str(got.exception))
 def test_quota_expiry_and_restrictions_are_distinguished(self):
  for code,message,expected in [(429,'','лимит'),(403,'quota exceeded','лимит'),(403,'key expired','истёк'),(403,'referrer restriction','ограничений'),(401,'invalid key','не принят')]:
   self.assertIn(expected,sources.digis_key_error(code,{'meta':{'error':{'message':message}}}))
 def test_curl_fallback_preserves_http_error(self):
  response=subprocess.CompletedProcess([],0,stdout=b'{"meta":{"code":403}}\n403',stderr=b'')
  with patch('urllib.request.urlopen',side_effect=urllib.error.URLError('ssl')),patch('subprocess.run',return_value=response) as run:
   with self.assertRaises(RuntimeError) as got:sources.check_2gis_key('fake-secret-key')
  self.assertIn('403',str(got.exception));self.assertNotIn('fake-secret-key',' '.join(run.call_args.args[0]))
 def test_successful_key(self):
  data=io.BytesIO(b'{"meta":{"code":200},"result":{"items":[]}}')
  with patch('urllib.request.urlopen',return_value=data):sources.check_2gis_key('fake-key')
 def test_paste_format_mistake_does_not_send_network_request(self):
  with patch('urllib.request.urlopen') as request:
   for value in ('"fake"','export KEY=fake','https://site/key','fake key'):
    with self.assertRaises(RuntimeError):sources.check_2gis_key(value)
  request.assert_not_called()
 def test_network_error_does_not_echo_stderr(self):
  with patch('urllib.request.urlopen',side_effect=urllib.error.URLError('no network')),patch('subprocess.run',side_effect=subprocess.CalledProcessError(6,['curl'],stderr=b'fake-secret-key')):
   with self.assertRaises(RuntimeError) as got:sources.check_2gis_key('fake-secret-key')
  self.assertIn('соединиться',str(got.exception));self.assertNotIn('fake-secret-key',str(got.exception))
if __name__=='__main__':unittest.main()
