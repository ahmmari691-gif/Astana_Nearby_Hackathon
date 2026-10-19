# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
import app
from understanding import local_profile,merge_profiles,clean_profile
from test_app import BASE,place

class UnlimitedTimeTests(unittest.TestCase):
 def test_missing_time_does_not_discard_long_visit(self):
  data=dict(BASE,query='Хочу кино',radius=2500);data.pop('minutes')
  rows,_=app.retrieve(data,[place(kind='cinema')])
  self.assertEqual(len(rows),1)
 def test_no_time_question(self):
  data=dict(BASE,query='Хочу кино рядом');data.pop('minutes');data.pop('radius')
  with patch.object(app,'KEY',''),patch.object(app,'DIGIS_KEY',''),patch.object(app,'dataset',return_value={'places':[]}):result=app.recommend(data)
  self.assertNotIn('needs_clarification',result);self.assertIsNone(result['filters']['minutes']);self.assertEqual(result['filters']['radius'],1000)
 def test_unlimited_text_overrides_stale_form_limit(self):
  data=dict(BASE,query='Хочу кино, время не ограничено',minutes=30)
  rows,_=app.retrieve(data,[place(kind='cinema')]);self.assertEqual(len(rows),1)
 def test_unlimited_survives_model_inventing_a_limit(self):
  p=merge_profiles(local_profile('Хочу музей, неограниченное время'),clean_profile({'include':['museum'],'max_minutes':60}))
  self.assertIsNone(p['max_minutes']);self.assertTrue(p['time_unlimited'])
 def test_explicit_time_still_honored(self):
  rows,_=app.retrieve(dict(BASE,query='Хочу кино на 30 минут'),[place(kind='cinema')]);self.assertEqual(rows,[])
 def test_no_four_hour_cap(self):
  self.assertEqual(local_profile('Хочу прогулку на 6 часов')['max_minutes'],360)
  self.assertEqual(app.validate(dict(BASE,minutes=360))[2],360)

if __name__=='__main__':unittest.main()
