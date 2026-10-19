# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock
import group_planning as groups
from understanding import clean_profile
QUERY='Нас четверо, мы возле Байтерека. Хотим погулять, посмотреть архитектуру и выпить кофе. Есть два часа, рядом'
class GroupResponseRepair(unittest.TestCase):
 def setUp(self):self.group=groups.context({'query':QUERY});self.shared=clean_profile({'include':['architecture','cafe'],'max_minutes':120,'max_distance_m':1000})
 def test_shared_request_does_not_require_repeated_member_profiles(self):
  p,g,semantic=groups.analyze(QUERY,'ru',self.group,lambda _:{'shared_profile':self.shared},'fake')
  self.assertTrue(semantic);self.assertEqual([m['request'] for m in g['members']],['']*4)
  self.assertIn('architecture',p['include']);self.assertIn('cafe',p['include'])
 def test_null_entries_are_allowed(self):
  p,g,semantic=groups.analyze(QUERY,'ru',self.group,lambda _:{'shared_profile':self.shared,'member_requests':[None]*4,'member_profiles':[None]*4},'fake')
  self.assertTrue(semantic);self.assertEqual(len(g['members']),4)
 def test_flat_shared_profile_is_harmless_for_common_request(self):
  self.assertTrue(groups.analyze(QUERY,'ru',self.group,lambda _:self.shared,'fake')[2])
 def test_one_retry_for_wrong_schema_then_success(self):
  complete=Mock(side_effect=[{'shared_profile':None},{'shared_profile':self.shared}])
  self.assertTrue(groups.analyze(QUERY,'ru',self.group,complete,'fake')[2]);self.assertEqual(complete.call_count,2)
 def test_retry_for_truncated_json(self):
  complete=Mock(side_effect=[ValueError('Truncated model response'),{'shared_profile':self.shared}])
  self.assertTrue(groups.analyze(QUERY,'ru',self.group,complete,'fake')[2]);self.assertEqual(complete.call_count,2)
 def test_quota_errors_are_not_retried(self):
  complete=Mock(side_effect=RuntimeError('quota'))
  with self.assertRaises(RuntimeError):groups.analyze(QUERY,'ru',self.group,complete,'fake')
  self.assertEqual(complete.call_count,1)
 def test_distributed_requests_cannot_silently_disappear(self):
  q='Нас четверо: двое хотят кофе, двое музей, рядом'
  complete=Mock(return_value={'shared_profile':self.shared})
  with self.assertRaises(ValueError):groups.analyze(q,'ru',groups.context({'query':q}),complete,'fake')
  self.assertEqual(complete.call_count,2)
 def test_case_punctuation_and_whitespace_are_not_invented_interests(self):
  q='Нас четверо: двое хотят КОФЕ, двое — музей, рядом'
  raw={'shared_profile':self.shared,'member_requests':['кофе','кофе','Музей','Музей'],'member_profiles':[None]*4}
  _,g,semantic=groups.analyze(q,'ru',groups.context({'query':q}),lambda _:raw,'fake')
  self.assertTrue(semantic);self.assertEqual(len(g['members']),4)
 def test_unknown_category_remains_an_error(self):
  bad=dict(self.shared,include=['invented_place'])
  with self.assertRaises(ValueError):groups.analyze(QUERY,'ru',self.group,lambda _:{'shared_profile':bad},'fake')
if __name__=='__main__':unittest.main()
