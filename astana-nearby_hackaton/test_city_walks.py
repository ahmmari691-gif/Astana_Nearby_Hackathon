# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
import app,sources
from understanding import local_profile,merge_profiles,clean_profile
from test_app import BASE,place
from test_verification import normalized

class CityWalkTests(unittest.TestCase):
 def test_unspecified_walk_asks_style_before_search(self):
  with patch.object(app,'KEY',''),patch.object(app,'search_2gis') as search:
   result=app.recommend(dict(BASE,query='Хочу погулять 60 минут'))
  self.assertTrue(result['needs_clarification']);self.assertIn('архитектура',result['question']);search.assert_not_called()
 def test_architecture_answer_overrides_default_parks(self):
  p=local_profile('Хочу прогулку\nУточнение: городская архитектура')
  self.assertFalse(p['needs_clarification']);self.assertIn('architecture',p['include']);self.assertNotIn('park',p['include'])
  semantic=clean_profile({'include':['park']})
  self.assertIn('architecture',merge_profiles(p,semantic)['include'])
 def test_green_answer_still_allows_waterfront(self):
  p=local_profile('Хочу прогулку\nУточнение: зелень и тишина')
  self.assertFalse(p['needs_clarification']);self.assertIn('park',p['include']);self.assertIn('promenade',p['include'])
 def test_lively_walk_has_no_park_default(self):
  p=local_profile('Хочу прогулку по оживлённым улицам')
  self.assertIn('pedestrian',p['include']);self.assertNotIn('park',p['include'])
 def test_new_categories_and_geo_links(self):
  for name,kind in [('Набережная','promenade'),('Бульвар','boulevard'),('Площадь','square'),('Пешеходная улица','pedestrian'),('Памятник архитектуры','architecture')]:
   p=normalized(name=name,name_ex={'primary':name,'extension':''},rubrics=[{'name':name}],type='attraction')
   self.assertEqual(p['kind'],kind);self.assertIn('/geo/',p['source']);self.assertTrue(sources.safe_source_url(p['source']))
 def test_nearest_walks_keep_distance_priority(self):
  rows,_=app.retrieve(dict(BASE,query='Хочу прогулку'),[place(),place('node/2'),place('node/3'),place('node/4',kind='promenade'),place('node/5',kind='square')])
  self.assertEqual([row['distance_m'] for row in rows],sorted(row['distance_m'] for row in rows))
 def test_night_walk_is_not_nightclub(self):
  self.assertNotIn('nightclub',local_profile('Хочу ночную прогулку')['include'])

if __name__=='__main__':unittest.main()
