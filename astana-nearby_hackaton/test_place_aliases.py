# -*- coding: utf-8 -*-
import unittest,urllib.parse
from unittest.mock import patch
import text_location

class PlaceAliasTests(unittest.TestCase):
 def test_russian_names_and_declensions(self):
  for name,expected in [('керуен','Keruen'),('керуена','Keruen'),('Керуен Сити','KeruenCity'),('мега','MEGA'),('меге','MEGA'),('Мега Силк Вей','MEGA Silk Way'),('мега силквей','MEGA Silk Way'),('ТЦ Керуен','Keruen')]:
   with self.subTest(name=name):self.assertEqual(text_location.name_variants(name)[0],expected)
 def test_start_without_ya(self):
  self.assertEqual(text_location.extract_start('Нахожусь в меге, хочу кофе'),'меге')
  self.assertEqual(text_location.extract_start('Возле керуена, хочу погулять'),'керуена')
  self.assertEqual(text_location.extract_start('Керуен, хочу кофе'),'Керуен')
 def test_destination_is_not_start(self):
  self.assertIsNone(text_location.extract_start('Хочу пойти в Мегу'))
 def test_provider_receives_canonical_name(self):
  with patch.object(text_location,'provider_json',return_value={'meta':{'code':200},'result':{'items':[{'name':'Keruen','point':{'lat':51.128,'lon':71.43}}]}}) as provider:
   result=text_location.resolve_start('Я у керуена, хочу кофе','fake')
  query=urllib.parse.parse_qs(urllib.parse.urlsplit(provider.call_args[0][0]).query)['q'][0]
  self.assertEqual(query,'Астана Keruen');self.assertEqual(result['status'],'resolved')
 def test_ambiguous_mega_still_requires_selection(self):
  items=[{'name':'MEGA A','point':{'lat':51.1,'lon':71.4}},{'name':'MEGA B','point':{'lat':51.2,'lon':71.5}}]
  with patch.object(text_location,'provider_json',return_value={'meta':{'code':200},'result':{'items':items}}):result=text_location.resolve_start('Я в меге','fake')
  self.assertEqual(result['status'],'ambiguous')
 def test_not_found_canonical_tries_original(self):
  empty={'meta':{'code':404}};found={'meta':{'code':200},'result':{'items':[{'name':'Керуен','point':{'lat':51.128,'lon':71.43}}]}}
  with patch.object(text_location,'provider_json',side_effect=[empty,found]) as provider:result=text_location.resolve_start('Я у керуена','fake')
  self.assertEqual(provider.call_count,2);self.assertEqual(result['status'],'resolved')

if __name__=='__main__':unittest.main()
