# -*- coding: utf-8 -*-
import unittest,urllib.parse
from unittest.mock import patch
import app,sources
from understanding import local_profile
from test_app import BASE
from test_verification import normalized,raw
Q='Хочу прогуляться и увидеть что-нибудь интересное\nУточнение: рядом\nУточнение: оживлённые улицы'
class LivelyStreetTests(unittest.TestCase):
 def test_followup_selects_streets_within_one_km(self):
  p=local_profile(Q);self.assertEqual(p['include'],['pedestrian']);self.assertEqual(p['max_distance_m'],1000);self.assertFalse(p['needs_clarification'])
 def test_street_objects_are_not_discarded_or_claimed_pedestrian(self):
  p=normalized(type='street',name='улица Кенесары',name_ex={},rubrics=[])
  self.assertEqual(p['kind'],'street');self.assertIn('/geo/',p['source'])
  rows,_=app.retrieve(dict(BASE,query=Q),[p]);self.assertEqual(rows,[])
 def test_geo_names_preserve_waterfront_and_boulevard(self):
  for name,kind in [('набережная Есиль','promenade'),('бульвар Нуржол','boulevard')]:
   p=normalized(type='street',name=name,name_ex={},rubrics=[]);self.assertEqual(p['kind'],kind)
 def test_business_name_does_not_make_a_street(self):
  p=normalized(type='branch',name='улица Кофе',name_ex={'primary':'улица Кофе','extension':'кофейня'},rubrics=[{'name':'Кофейни'}])
  self.assertEqual(p['kind'],'cafe');self.assertEqual(app.retrieve(dict(BASE,query=Q),[p])[0],[])
 def test_provider_requests_nearest_street_type(self):
  sources._PROVIDER_CACHE.clear()
  with patch.object(sources,'provider_json',return_value={'meta':{'code':200},'result':{'items':[raw(type='street',name='улица Кенесары',name_ex={},rubrics=[])]}}) as request:
   rows=sources.search_2gis(dict(local_profile(Q),_nearby={'lat':BASE['lat'],'lon':BASE['lon']},_search_radius=1000),'fake')
  calls=[urllib.parse.parse_qs(urllib.parse.urlsplit(c.args[0]).query) for c in request.call_args_list]
  street=[c for c in calls if c.get('type')==['street,attraction']]
  self.assertTrue(street);self.assertEqual(street[0]['q'],['Астана пешеходная улица']);self.assertEqual(street[0]['sort'],['distance']);self.assertEqual(street[0]['radius'],['1000'])
  self.assertEqual(app.retrieve(dict(BASE,query=Q),rows)[0],[])
 def test_new_pedestrian_wording(self):
  p=local_profile(Q.replace('оживлённые','пешеходные'));self.assertEqual(p['include'],['pedestrian']);self.assertFalse(p['needs_clarification'])
 def test_confirmed_pedestrian_street_is_retained(self):
  p=normalized(type='street',name='Пешеходная улица',name_ex={},rubrics=[])
  rows,_=app.retrieve(dict(BASE,query=Q),[p]);self.assertEqual(len(rows),1);self.assertEqual(rows[0]['kind'],'pedestrian')
if __name__=='__main__':unittest.main()
