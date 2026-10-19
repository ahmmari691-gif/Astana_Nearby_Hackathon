# -*- coding: utf-8 -*-
import datetime,unittest
from unittest.mock import patch
import app
from understanding import local_profile,merge_profiles
from text_location import extract_start
from scenario_rules import open_for_visit
from test_app import BASE,place

QUERIES=[
'Я сейчас возле Mega Silk Way, хочу прогуляться 30–60 минут — что посоветуете?',
'Хочу тихое место с кофе и розеткой недалеко от меня.',
'Еду с ребёнком — где рядом есть детские площадки или музей с интерактивами?',
'Я - турист, у меня 2 часа перед вылетом: что можно посмотреть поблизости?',
'Ищу необычную ночную активность (последние пару часов).']

class RequestedScenarios(unittest.TestCase):
 def test_mega_walk_duration_and_origin(self):
  p=local_profile(QUERIES[0]);self.assertEqual(p['max_minutes'],60)
  self.assertNotIn('museum',p['include']);self.assertEqual(extract_start(QUERIES[0]),'Mega Silk Way')
  rows,_=app.retrieve(dict(BASE,query=QUERIES[0]),[place(),place('node/2',kind='museum'),place('node/3',lat=51.30)])
  self.assertEqual([r['kind'] for r in rows],['park']);self.assertTrue(all(r['total_minutes']<=60 for r in rows))
 def test_coffee_quiet_and_sockets_are_not_guaranteed(self):
  p=local_profile(QUERIES[1]);self.assertEqual(p['include'],['cafe'])
  self.assertTrue({'quiet','sockets'}<=set(p['unverified']))
  rows,_=app.retrieve(dict(BASE,query=QUERIES[1]),[place(kind='cafe'),place('node/2',kind='park')])
  self.assertEqual(len(rows),1);self.assertIn('не подтверждены',rows[0]['why'])
 def test_child_travel_is_not_food(self):
  p=local_profile(QUERIES[2]);self.assertNotIn('restaurant',p['include'])
  candidates=[place(kind='playground'),place('node/2',kind='museum'),place('node/3',kind='restaurant'),place('node/4',kind='museum',features=['Интерактивная экспозиция'])]
  rows,_=app.retrieve(dict(BASE,query=QUERIES[2]),candidates)
  self.assertEqual({r['id'] for r in rows},{'node/1','node/4'})
 def test_before_flight_does_not_offer_excursion(self):
  with patch.object(app,'KEY',''),patch.object(app,'DIGIS_KEY','fake'),patch.object(app,'dataset',return_value={'places':[place()]}),patch.object(app,'search_2gis') as request,patch.object(app,'verification_gate',return_value=([],'checked')):
   result=app.recommend(dict(BASE,query=QUERIES[3],minutes=120))
  self.assertEqual(result['items'],[]);self.assertIn('регистрацию',result['empty']);request.assert_not_called()
 def test_night_unknown_hours_excluded(self):
  self.assertEqual(local_profile(QUERIES[4])['max_minutes'],120)
  rows,_=app.retrieve(dict(BASE,query=QUERIES[4],minutes=120),[place(),place('node/2',kind='museum')])
  self.assertEqual(rows,[])
 def test_night_entire_visit_must_fit_schedule(self):
  now=datetime.datetime(2026,10,17,23,0,tzinfo=datetime.timezone(datetime.timedelta(hours=5)))
  p=place(schedule={'Sat':{'working_hours':[{'from':'20:00','to':'02:00'}]}})
  self.assertTrue(open_for_visit(p,5,40,now));self.assertFalse(open_for_visit(p,5,200,now))
  early=now.replace(hour=1)
  self.assertTrue(open_for_visit(place(schedule={'Fri':{'working_hours':[{'from':'20:00','to':'02:00'}]}}),5,40,early))
 def test_rejected_night_request_has_clear_reason(self):
  with patch.object(app,'KEY',''),patch.object(app,'DIGIS_KEY',''),patch.object(app,'dataset',return_value={'places':[]}):
   result=app.recommend(dict(BASE,query=QUERIES[4]))
  self.assertEqual(result['items'],[]);self.assertIn('ночного',result['empty'])

if __name__=='__main__':unittest.main()
