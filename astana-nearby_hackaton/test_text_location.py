# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
import app,text_location
from test_app import BASE

class TextLocationTests(unittest.TestCase):
 def test_start_is_not_destination(self):
  self.assertEqual(text_location.extract_start('Я у здании Экспо 2017, хочу что-то необычное'),'Экспо 2017')
  self.assertEqual(text_location.extract_start('Я стою возле Байтерека и хочу суши'),'Байтерека')
  self.assertEqual(text_location.extract_start('I am at EXPO, want sushi'),'EXPO')
  self.assertEqual(text_location.extract_start('Мен Экспо жанындамын, мұражайға барғым келеді'),'Экспо')
 def test_no_implicit_default_origin(self):
  data={k:v for k,v in BASE.items() if k not in ('lat','lon')}
  with patch.object(app,'DIGIS_KEY',''):
   result=app.recommend(dict(data,query='Хочу музей'))
  self.assertTrue(result['needs_location']);self.assertEqual(result['origin']['status'],'missing')
 def test_ambiguous_origin_requires_choice(self):
  items=[{'name':'Mall','point':{'lat':51.1,'lon':71.4}},{'name':'Other Mall','point':{'lat':51.2,'lon':71.5}}]
  with patch.object(text_location,'provider_json',return_value={'meta':{'code':200},'result':{'items':items}}):
   result=text_location.resolve_start('Я у торгового центра, хочу кофе','fake')
  self.assertEqual(result['status'],'ambiguous');self.assertEqual(len(result['choices']),2)
 def test_single_origin_resolves(self):
  item={'name':'EXPO','point':{'lat':51.089,'lon':71.407}}
  with patch.object(text_location,'provider_json',return_value={'meta':{'code':200},'result':{'items':[item]}}):
   result=text_location.resolve_start('Я у Экспо, хочу музей','fake')
  self.assertEqual(result['status'],'resolved');self.assertEqual(result['lat'],51.089)

if __name__=='__main__':unittest.main()
