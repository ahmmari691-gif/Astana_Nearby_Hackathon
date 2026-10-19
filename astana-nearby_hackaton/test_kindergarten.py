# -*- coding: utf-8 -*-
import unittest
import app
from test_verification import normalized
from test_app import BASE
from understanding import local_profile
class KindergartenTests(unittest.TestCase):
 def test_childcare_never_becomes_a_garden_or_playground(self):
  for label in ('Детские сады','Частный детский сад','Ясли-сад','Дошкольное образование','Kindergarten','Nursery','Балабақша'):
   p=normalized(rubrics=[{'name':label}],name_ex={'primary':'Test','extension':''},attribute_groups=[{'attributes':[{'name':'Детская площадка'}]}])
   self.assertEqual(p['kind'],'other',label)
   self.assertEqual(app.retrieve(dict(BASE,query='Парк или детская площадка рядом'),[p])[0],[],label)
 def test_old_misclassified_childcare_is_rejected(self):
  for kind in ('garden','park','kids_centre','playground'):
   p=normalized(rubrics=[{'name':'Детские сады'}]);p['kind']=kind
   self.assertEqual(app.retrieve(dict(BASE,query='Парк или детская площадка рядом'),[p])[0],[])
 def test_public_gardens_are_retained(self):
  for label in ('Ботанические сады','Сады','Gardens'):
   p=normalized(rubrics=[{'name':label}],name_ex={'primary':'Garden','extension':''})
   self.assertEqual(p['kind'],'garden',label)
   self.assertEqual(len(app.retrieve(dict(BASE,query='Ботанический сад рядом'),[p])[0]),1)
 def test_unrelated_word_is_not_a_garden(self):
  p=normalized(rubrics=[{'name':'Фасадные работы'}],name_ex={'primary':'Test','extension':''})
  self.assertEqual(p['kind'],'other')
 def test_childcare_request_is_not_a_walk(self):
  p=local_profile('Ищу детский сад рядом');self.assertNotIn('garden',p['include']);self.assertTrue(p['unsupported'])
  p=local_profile('Ищу парк рядом с детским садом');self.assertEqual(p['include'],['park']);self.assertFalse(p['unsupported'])
if __name__=='__main__':unittest.main()
