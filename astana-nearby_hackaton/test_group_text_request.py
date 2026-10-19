# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
import app,group_planning as groups
from text_location import extract_start
QUERY='Нас четверо, мы возле Байтерека. Хотим погулять, посмотреть архитектуру и выпить кофе. Есть два часа'
class TextGroupRequests(unittest.TestCase):
 def test_user_example_recognizes_group_origin_time_and_both_activities(self):
  context=groups.context({'query':QUERY});self.assertEqual(context['size'],4)
  self.assertEqual(extract_start(QUERY),'Байтерека')
  profile,plan,_=groups.analyze(QUERY,'ru',context)
  self.assertEqual(profile['max_minutes'],120)
  self.assertIn('architecture',profile['include']);self.assertIn('cafe',profile['include'])
  self.assertEqual([m['request'] for m in plan['members']],['']*4)
 def test_group_survives_radius_clarification_without_extra_form_fields(self):
  query=QUERY+'\nУточнение: рядом'
  group=groups.context({'query':query});profile,_,_=groups.analyze(query,'ru',group)
  self.assertEqual(group['size'],4);self.assertEqual(profile['max_distance_m'],1000);self.assertFalse(profile['needs_clarification'])
 def test_plural_origin_fallback_resolves_before_preferences(self):
  with patch('text_location.resolve_start',return_value={'status':'resolved','lat':51.1282,'lon':71.4304,'name':'Байтерек','address':''}) as resolve,patch.object(app,'KEY',''),patch.object(app,'DIGIS_KEY',''),patch.object(app,'dataset',return_value={'places':[]}):
   result=app.recommend({'query':QUERY+'\nУточнение: рядом'})
  resolve.assert_called_once();self.assertEqual(result['group']['size'],4);self.assertEqual(result['filters']['minutes'],120)
 def test_english_plural_origin(self):self.assertEqual(extract_start('There are four of us, we are near Baiterek, want coffee'),'Baiterek')
if __name__=='__main__':unittest.main()
