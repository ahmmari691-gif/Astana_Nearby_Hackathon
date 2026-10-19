# -*- coding: utf-8 -*-
import copy,json,unittest,urllib.parse
from unittest.mock import patch
import app,sources,group_planning as groups
from understanding import clean_profile,local_profile
from test_app import BASE
from test_verification import normalized

def group(*requests):return {'size':len(requests),'requests':list(requests)}
def point(ident,kind,lat=51.1282):return normalized(id=ident,point={'lat':lat,'lon':71.4304},rubrics=[{'name':{'museum':'Музеи','cafe':'Кафе','park':'Парки'}[kind]}],name_ex={'primary':ident,'extension':''})

class GroupTests(unittest.TestCase):
 def test_text_size_detection(self):
  for query,size in [('Нас четверо, хотим кофе рядом',4),('Нас 3, рядом музей',3),('Мы впятером',5),('Group of four, coffee nearby',4),('Біз төрт адам',4)]:self.assertEqual(groups.context({'query':query})['size'],size)
 def test_invalid_sizes_and_preferences_are_rejected(self):
  for raw in ({'enabled':True,'size':True},{'enabled':True,'size':9},{'enabled':True,'size':3,'preferences':['x']*4},{'enabled':True,'size':3,'preferences':[42]}):
   with self.assertRaises(ValueError):groups.context({'group':raw})
 def test_empty_members_are_not_assigned_invented_wishes(self):
  p,g,_=groups.analyze('Хотим кофе рядом','ru',group('','',''))
  self.assertEqual(p['include'],['cafe']);self.assertEqual([m['request'] for m in g['members']],['','',''])
 def test_different_activities_are_alternatives(self):
  p,g,_=groups.analyze('Нас четверо, рядом','ru',group('Кофе','Музей','Музей','Музей'))
  self.assertEqual(set(p['include']),{'cafe','museum'});self.assertEqual(p['max_distance_m'],1000);self.assertFalse(p['needs_clarification'])
 def test_different_cuisines_remain_mandatory(self):
  p,_,_=groups.analyze('Рядом','ru',group('Корейская еда','Итальянская еда','Кофе'))
  self.assertEqual({r['value'] for r in p['food_requirements']},{'korean','italian'})
 def test_tightest_limits_and_negatives_are_preserved(self):
  p,_,_=groups.analyze('Рядом','ru',group('Музей, 30 минут','Музей, до 500 м','Не хочу в бар, музей'))
  self.assertEqual(p['max_minutes'],30);self.assertEqual(p['max_distance_m'],500);self.assertIn('bar',p['exclude'])
 def test_environment_conflict_asks_instead_of_guessing(self):
  p,_,_=groups.analyze('Рядом','ru',group('В помещении, музей','На улице, парк','Кофе'))
  self.assertTrue(p['needs_clarification'])
 def test_universal_veto_cannot_be_outvoted(self):
  p,_,_=groups.analyze('Рядом','ru',group('Кофе','Кофе','Не хочу кофе'))
  self.assertIn('cafe',p['exclude'])
 def test_three_museum_votes_outrank_one_closer_cafe(self):
  p,g,_=groups.analyze('Рядом','ru',group('Кофе','Музей','Музей','Музей'))
  data=dict(BASE,query='Рядом',_profile=p)
  items,_=app.retrieve(data,[point('111111','cafe'),point('222222','museum',51.130)])
  ranked=groups.rank(items,g,data,app.retrieve)
  self.assertEqual(ranked[0]['kind'],'museum');self.assertEqual(ranked[0]['group_match']['count'],3);self.assertEqual(ranked[1]['group_match']['count'],1)
 def test_unconfirmed_amenity_is_not_a_confirmed_match(self):
  p,g,_=groups.analyze('Рядом','ru',group('Кофе с розеткой','Кофе',''))
  items,_=app.retrieve(dict(BASE,query='Рядом',_profile=p),[point('111111','cafe')])
  match=groups.rank(items,g,BASE,app.retrieve)[0]['group_match']
  self.assertEqual(match['uncertain'],[1]);self.assertEqual(match['matched'],[2]);self.assertEqual(match['unspecified'],[3])
 def test_source_search_covers_coffee_and_museums(self):
  sources._PROVIDER_CACHE.clear()
  with patch.object(sources,'provider_json',return_value={'meta':{'code':200},'result':{'items':[]}}) as request:sources.search_2gis({'include':['cafe','museum']},'fake')
  queries=[urllib.parse.parse_qs(urllib.parse.urlsplit(c.args[0]).query)['q'][0] for c in request.call_args_list]
  self.assertEqual(queries,['Астана Кофейни','Астана Кафе','Астана музеи'])
 def test_ai_cannot_invent_members_or_preferences(self):
  raw={'shared_profile':clean_profile({}),'member_requests':['Кофе','музей','Пицца'],'member_profiles':[clean_profile({})]*3}
  with self.assertRaises(ValueError):groups.analyze('Рядом','ru',group('Кофе','',''),lambda _:raw,'fake')
 def test_ai_assigns_explicit_free_text_preferences(self):
  query='Нас четверо: двое хотят кофе, двое музей, рядом'
  raw={'shared_profile':clean_profile({'max_distance_m':1000}),'member_requests':['кофе','кофе','музей','музей'],'member_profiles':[clean_profile({'include':[k]}) for k in ('cafe','cafe','museum','museum')]}
  p,g,semantic=groups.analyze(query,'ru',group('','','',''),lambda _:raw,'fake')
  self.assertTrue(semantic);self.assertEqual([m['request'] for m in g['members']],raw['member_requests']);self.assertEqual(set(p['include']),{'cafe','museum'})
 def test_runtime_groups_and_single_user_both_work(self):
  rows=[point('111111','cafe'),point('222222','museum',51.130)]
  with patch.object(app,'KEY',''),patch.object(app,'DIGIS_KEY','fake'),patch.object(app,'search_2gis',return_value=rows),patch.object(app,'dataset',return_value={'places':[]}),patch('request_dataset.save_batch'):
   result=app.recommend(dict(BASE,query='Рядом',group={'enabled':True,'size':4,'preferences':['Кофе','Музей','Музей','Музей']}))
  self.assertEqual(result['group']['size'],4);self.assertEqual(result['items'][0]['kind'],'museum');self.assertTrue(any('вместимость' in w for w in result['warnings']))
 def test_shared_time_in_words_is_preserved(self):
  p,_,_=groups.analyze('Нас четверо, рядом, есть два часа','ru',group('Кофе','Музей','Музей','Музей'))
  self.assertEqual(p['max_minutes'],120)
 def test_group_count_is_not_a_specific_food(self):
  p,_,_=groups.analyze('Нас четверо, хотим поесть рядом','ru',group('','','',''))
  self.assertFalse(p['food_unverified'])

if __name__=='__main__':unittest.main()
