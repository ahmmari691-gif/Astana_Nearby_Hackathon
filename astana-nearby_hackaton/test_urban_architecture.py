# -*- coding: utf-8 -*-
import unittest
import app
from test_verification import normalized
from test_app import BASE
from understanding import local_profile
QUERY='Хочу прогуляться и увидеть что-нибудь интересное\nУточнение: рядом\nУточнение: городская архитектура'
class UrbanArchitectureTests(unittest.TestCase):
 def test_full_followup_query_is_understood(self):
  p=local_profile(QUERY);self.assertIn('architecture',p['include']);self.assertEqual(p['max_distance_m'],1000);self.assertFalse(p['needs_clarification'])
 def test_real_2gis_categories_are_not_discarded(self):
  for label,kind in [('Интересные здания','architecture'),('Памятники и скульптуры','attraction'),('Памятные доски','attraction'),('Фонтаны','attraction')]:
   p=normalized(rubrics=[{'name':label}],name_ex={'primary':'','extension':''},name='')
   self.assertEqual(p['kind'],kind,label);self.assertTrue(p['name'])
   self.assertEqual(len(app.retrieve(dict(BASE,query=QUERY),[p])[0]),1,label)
 def test_interesting_theatre_can_be_an_outdoor_architecture_stop(self):
  p=normalized(rubrics=[{'name':'Интересные здания'},{'name':'Театры'}],name_ex={'primary':'Театр','extension':'театр'})
  self.assertEqual(p['kind'],'theatre')
  rows,_=app.retrieve(dict(BASE,query=QUERY),[p]);self.assertEqual(rows[0]['kind'],'architecture')
  self.assertIn('общедоступной',rows[0]['action'])
 def test_theatre_without_architecture_evidence_is_not_substituted(self):
  p=normalized(rubrics=[{'name':'Театры'}],name_ex={'primary':'Театр','extension':'театр'})
  self.assertEqual(app.retrieve(dict(BASE,query=QUERY),[p])[0],[])
 def test_architecture_office_not_a_landmark(self):
  p=normalized(rubrics=[{'name':'Архитектурное проектирование'}],name_ex={'primary':'Бюро','extension':''})
  self.assertEqual(app.retrieve(dict(BASE,query=QUERY),[p])[0],[])
 def test_radius_and_low_rating_filters_still_apply(self):
  p=normalized(point={'lat':51.16,'lon':71.43},rubrics=[{'name':'Интересные здания'}],name_ex={'primary':'Здание','extension':''})
  self.assertEqual(app.retrieve(dict(BASE,query=QUERY),[p])[0],[])
  p=normalized(rubrics=[{'name':'Интересные здания'}],name_ex={'primary':'Здание','extension':''},reviews={'general_rating':2.5})
  self.assertEqual(app.retrieve(dict(BASE,query=QUERY,_min_rating=3),[p])[0],[])
if __name__=='__main__':unittest.main()
