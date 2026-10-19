# -*- coding: utf-8 -*-
import unittest
import app
from group_planning import context,analyze,rank
from test_app import BASE,place

QUERY='Нас четверо возле Байтерека. Хотим посмотреть архитектуру и выпить кофе. Есть два часа, ищем до 2,5 км.'

class GroupActivityCoverage(unittest.TestCase):
 def data(self):
  profile,group,_=analyze(QUERY,'ru',context({'query':QUERY}))
  profile['_group_search']=True
  return dict(BASE,query=QUERY,minutes=120,_profile=profile,_limit=15),group
 def candidates(self):
  return [place('architecture-'+str(i),kind='architecture',lat=BASE['lat']+i*.0001) for i in range(20)]+[place('coffee',kind='cafe',category='Кофейни',lat=BASE['lat']+.004)]
 def test_exact_request_keeps_coffee_category(self):
  data,_=self.data()
  self.assertIn('cafe',data['_profile']['include'])
  self.assertIn('architecture',data['_profile']['include'])
 def test_coffee_survives_candidate_limit_and_final_five(self):
  data,group=self.data()
  rows,_=app.retrieve(data,self.candidates())
  self.assertEqual(len(rows),15)
  self.assertIn('coffee',[p['id'] for p in rows])
  result=rank(rows,group,data,app.retrieve)
  self.assertEqual(len(result),5)
  self.assertIn('coffee',[p['id'] for p in result])
  self.assertEqual([p['distance_m'] for p in result],sorted(p['distance_m'] for p in result))
 def test_diversity_does_not_bypass_radius(self):
  data,group=self.data();data['radius']=100
  rows,_=app.retrieve(data,self.candidates())
  self.assertNotIn('coffee',[p['id'] for p in rank(rows,group,data,app.retrieve)])
 def test_single_activity_remains_nearest_first(self):
  data,group=self.data();data['_profile']['include']=['architecture']
  rows,_=app.retrieve(data,self.candidates())
  self.assertEqual([p['id'] for p in rank(rows,group,data,app.retrieve)],['architecture-'+str(i) for i in range(5)])

if __name__=='__main__':unittest.main()
