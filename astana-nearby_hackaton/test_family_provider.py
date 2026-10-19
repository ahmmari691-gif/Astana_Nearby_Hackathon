# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
import app
from understanding import local_profile
from test_verification import normalized
from test_app import BASE
from test_scenarios import QUERIES

class FamilyProviderRegression(unittest.TestCase):
 def test_real_plural_museum_rubric(self):
  p=normalized(rubrics=[{'name':'Музеи'}],name_ex={'primary':'Музей','extension':''},attribute_groups=[{'attributes':[{'name':'Интерактивный экспонат'}]}])
  self.assertEqual(p['kind'],'museum')
  rows,_=app.retrieve(dict(BASE,query=QUERIES[2]),[p])
  self.assertEqual(len(rows),1)
 def test_explicit_playground_in_park_is_accepted(self):
  p=normalized(rubrics=[{'name':'Парки'}],name_ex={'primary':'Парк','extension':''},attribute_groups=[{'attributes':[{'name':'Детские площадки'}]}])
  rows,_=app.retrieve(dict(BASE,query=QUERIES[2]),[p])
  self.assertEqual(len(rows),1);self.assertIn('отмечена детская площадка',rows[0]['why'])
 def test_no_feature_does_not_imply_playground(self):
  for feature in ('','Нет детских площадок','Без детских площадок'):
   p=normalized(rubrics=[{'name':'Парки'}],name_ex={'primary':'Парк','extension':''},attribute_groups=[{'attributes':[{'name':feature}]}])
   self.assertEqual(app.retrieve(dict(BASE,query=QUERIES[2]),[p])[0],[])
 def test_playground_does_not_bypass_radius(self):
  p=normalized(point={'lat':51.16,'lon':71.43},rubrics=[{'name':'Парки'}],name_ex={'primary':'Парк','extension':''},attribute_groups=[{'attributes':[{'name':'Детские площадки'}]}])
  self.assertEqual(app.retrieve(dict(BASE,query=QUERIES[2]),[p])[0],[])
 def test_semantic_empty_result_has_truthful_nonfood_reason(self):
  profile=local_profile(QUERIES[2]);profile['summary']='Площадки или интерактивные музеи рядом'
  with patch.object(app,'KEY','fake'),patch.object(app,'DIGIS_KEY','fake'),patch.object(app,'ai_profile',return_value=profile),patch.object(app,'dataset',return_value={'places':[]}),patch.object(app,'search_2gis',return_value=[]),patch.object(app,'verification_gate',return_value=([],'checked')),patch('request_dataset.save_batch'):
   result=app.recommend(dict(BASE,query=QUERIES[2],use_ai=True))
  self.assertEqual(result['understanding_mode'],'semantic')
  self.assertIn('ИИ разобрал',result['note']);self.assertNotIn('еда',result['empty'])
  self.assertIn('радиус',result['empty'])

if __name__=='__main__':unittest.main()
