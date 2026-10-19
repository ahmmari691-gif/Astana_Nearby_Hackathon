# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
import app,sources
from categories import EXTRA
from understanding import local_profile,clean_profile
from test_app import BASE

class ExtraCategoryTests(unittest.TestCase):
 def test_every_extra_category_has_parser_and_model_support(self):
  for kind,value in EXTRA.items():
   with self.subTest(kind=kind):
    profile=local_profile('Хочу '+value[0]);self.assertIn(kind,profile['include']);self.assertFalse(profile['unsupported']);clean_profile(profile)
 def test_cinema_is_not_theatre(self):
  self.assertEqual(local_profile('Хочу в кинотеатр')['include'],['cinema'])
 def test_waterpark_is_not_a_park(self):
  self.assertEqual(local_profile('Хочу в аквапарк')['include'],['waterpark'])
 def test_unclear_request_asks_before_provider_search(self):
  with patch.object(app,'KEY',''),patch.object(app,'search_2gis') as search:
   result=app.recommend(dict(BASE,query='Хочу что-нибудь необычное'))
  self.assertTrue(result['needs_clarification']);self.assertTrue(result['question']);search.assert_not_called()
 def test_clarification_answer_preserves_original_and_resolves_intent(self):
  profile=local_profile('Хочу что-нибудь необычное\nУточнение: хочу боулинг')
  self.assertFalse(profile['needs_clarification']);self.assertEqual(profile['include'],['bowling'])
 def test_semantic_uncertainty_asks_before_search(self):
  profile=local_profile('Хочу отдых');profile.update(needs_clarification=True,clarification='Спокойный или активный отдых?')
  with patch.object(app,'KEY','fake'),patch.object(app,'ai_profile',return_value=profile),patch.object(app,'search_2gis') as search:
   result=app.recommend(dict(BASE,query='Хочу отдых',use_ai=True))
  self.assertEqual(result['question'],'Спокойный или активный отдых?');search.assert_not_called()

if __name__=='__main__':unittest.main()
