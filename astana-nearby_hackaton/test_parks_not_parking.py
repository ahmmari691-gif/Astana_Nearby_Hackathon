# -*- coding: utf-8 -*-
import unittest
import app
from understanding import local_profile,PATTERNS
from test_verification import normalized
from test_app import BASE
import re
QUERY='Я с ребёнком, ищу парк или детскую площадку рядом'
class ParkParkingTests(unittest.TestCase):
 def test_exact_request_has_only_requested_categories(self):
  p=local_profile(QUERY)
  self.assertEqual(set(p['include']),{'park','playground'});self.assertEqual(p['max_distance_m'],1000)
 def test_parking_rubrics_never_become_parks(self):
  for label in ('Парковки','Парковка','Паркинги','Автостоянки','Parking','Car parks','Автопарки'):
   p=normalized(rubrics=[{'name':label}],name_ex={'primary':'Точка','extension':''})
   self.assertEqual(p['kind'],'other',label)
   self.assertEqual(app.retrieve(dict(BASE,query=QUERY),[p])[0],[],label)
 def test_real_parks_are_retained(self):
  for label in ('Парки','Скверы','Park','Parks','Саябақтар'):
   p=normalized(rubrics=[{'name':label}],name_ex={'primary':'Место','extension':''})
   self.assertEqual(p['kind'],'park',label)
   self.assertEqual(len(app.retrieve(dict(BASE,query=QUERY),[p])[0]),1,label)
 def test_old_incorrectly_classified_catalogue_row_is_rejected(self):
  p=normalized(rubrics=[{'name':'Парковки'}]);p['kind']='park'
  self.assertEqual(app.retrieve(dict(BASE,query=QUERY),[p])[0],[])
 def test_park_with_parking_amenity_is_still_park(self):
  p=normalized(rubrics=[{'name':'Парки'}],name_ex={'primary':'Парк','extension':'парк с парковкой'},attribute_groups=[{'attributes':[{'name':'Парковка'}]}])
  self.assertEqual(p['kind'],'park');self.assertEqual(len(app.retrieve(dict(BASE,query=QUERY),[p])[0]),1)
 def test_parking_words_do_not_explicitly_match_park_query(self):
  for text in ('парковка','парковки','паркинг','parking','автопарк'):
   self.assertIsNone(re.search(PATTERNS['park'],text,re.I),text)

if __name__=='__main__':unittest.main()
