# -*- coding: utf-8 -*-
import unittest,urllib.parse
from unittest.mock import patch
import app,sources
from understanding import local_profile,merge_profiles,clean_profile
from test_app import BASE
from test_verification import normalized
class CoffeeVenueTests(unittest.TestCase):
 def test_simple_coffee_stays_cafe_even_if_ai_broadens(self):
  p=merge_profiles(local_profile('Хочу кофе рядом'),clean_profile({'include':['restaurant','cafe']}))
  self.assertEqual(p['include'],['cafe']);self.assertTrue(p['coffee_venues_only'])
 def test_coffee_shops_cafes_and_coffee_chains_are_kept(self):
  for label in ('Кофейни','Кафе','Сеть кофеен','Coffee shop','Coffee chain'):
   p=normalized(rubrics=[{'name':label}],name_ex={'primary':'Точка','extension':''})
   self.assertEqual(p['kind'],'cafe',label)
   self.assertEqual(len(app.retrieve(dict(BASE,query='Хочу кофе рядом'),[p])[0]),1,label)
 def test_fast_food_and_restaurant_are_not_coffee_venues(self):
  for label in ('Кафе быстрого питания','Fast food cafe','Рестораны','Бургерные','Столовые'):
   p=normalized(rubrics=[{'name':label}],name_ex={'primary':'Кофе','extension':''},description='У нас продаётся кофе')
   self.assertEqual(app.retrieve(dict(BASE,query='Хочу кофе рядом'),[p])[0],[],label)
 def test_actual_coffee_rubric_survives_multiple_food_categories(self):
  p=normalized(rubrics=[{'name':'Рестораны'},{'name':'Кофейни'}],name_ex={'primary':'Coffee','extension':''})
  self.assertEqual(len(app.retrieve(dict(BASE,query='Хочу кофе рядом'),[p])[0]),1)
 def test_coffee_queries_search_actual_venue_types(self):
  sources._PROVIDER_CACHE.clear()
  with patch.object(sources,'provider_json',return_value={'meta':{'code':200},'result':{'items':[]}}) as request:sources.search_2gis(local_profile('Хочу кофе рядом'),'fake')
  labels=[urllib.parse.parse_qs(urllib.parse.urlsplit(c.args[0]).query)['q'][0] for c in request.call_args_list]
  self.assertEqual(labels,['Астана Кофейни','Астана Кафе'])
 def test_food_requirements_are_not_lost_when_coffee_is_requested(self):
  p=local_profile('Хочу кофе и суши рядом');self.assertFalse(p['coffee_venues_only']);self.assertTrue(p['food_requirements'])
 def test_real_cafe_rubric_with_dumpling_house_type_is_excluded(self):
  p=normalized(rubrics=[{'name':'Кафе'}],name_ex={'primary':'Лепим и варим','extension':'пельменная'})
  self.assertEqual(p['kind'],'cafe')
  self.assertEqual(app.retrieve(dict(BASE,query='Хочу кофе рядом'),[p])[0],[])
 def test_old_cached_short_description_is_checked(self):
  p=normalized(rubrics=[{'name':'Кафе'}],name_ex={'primary':'Лепим и варим','extension':''},description='пельменная')
  p.pop('venue_type',None)
  self.assertEqual(app.retrieve(dict(BASE,query='Хочу кофе рядом'),[p])[0],[])
 def test_cafe_menu_mention_does_not_change_venue_type(self):
  p=normalized(rubrics=[{'name':'Кофейни'}],name_ex={'primary':'Кофейня','extension':'кофейня'},description='В меню кофе, пельмени и десерты.')
  self.assertEqual(len(app.retrieve(dict(BASE,query='Хочу кофе рядом'),[p])[0]),1)
 def test_dumpling_request_can_still_recommend_dumpling_house(self):
  p=normalized(rubrics=[{'name':'Кафе'}],name_ex={'primary':'Лепим и варим','extension':'пельменная'},attribute_groups=[{'attributes':[{'name':'Пельмени'}]}])
  self.assertEqual(len(app.retrieve(dict(BASE,query='Хочу пельмени рядом'),[p])[0]),1)
 def test_coffee_drink_names(self):
  for q in ('Хочу капучино рядом','Хочу латте рядом','Espresso nearby'):
   p=local_profile(q);self.assertEqual(p['include'],['cafe']);self.assertTrue(p['coffee_venues_only'])
if __name__=='__main__':unittest.main()
