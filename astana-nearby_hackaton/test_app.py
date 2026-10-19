import unittest
from unittest.mock import patch
import app
from understanding import local_profile, clean_profile, merge_profiles

def place(id='node/1',kind='park',lat=51.1282,lon=71.4304,**kwargs):
    p={'id':id,'kind':kind,'name':id,'lat':lat,'lon':lon,'category':kind,'description':'','hours':None,'wheelchair':None,'why':'Подходит для прогулки; расчётное время укладывается в ваш бюджет.','hours_status':'Открытие сейчас не подтверждено','action':'Уточните доступность и выберите короткое посещение.','source':'https://www.openstreetmap.org/'+id}
    p.update(kwargs);return p
BASE={'lat':51.1282,'lon':71.4304,'minutes':60,'radius':2500,'query':'Прогулка в парке','use_ai':False}
class RetrievalTests(unittest.TestCase):
    def test_walk_is_not_family_substring(self):
        _,intent=app.retrieve(dict(BASE,query='Хочу увидеть что-нибудь интересное'),[])
        self.assertEqual(intent,'walk')
    def test_radius_and_time_are_hard_limits(self):
        results,_=app.retrieve(BASE,[place(),place('node/2',lon=71.48),place('node/3',kind='museum',lon=71.45)])
        self.assertEqual([p['id'] for p in results],['node/1'])
    def test_no_invented_accessibility(self):
        results,_=app.retrieve(dict(BASE,accessible=True),[place(),place('node/2',wheelchair='yes')])
        self.assertEqual([p['id'] for p in results],['node/2'])
    def test_no_museums_negation(self):
        results,_=app.retrieve(dict(BASE,query='Прогулка без музеев'),[place(),place('node/2',kind='museum')])
        self.assertTrue(all(p['kind']!='museum' for p in results))
    def test_rain_avoids_outdoors(self):
        results,_=app.retrieve(dict(BASE,weather='rain',query='Хочу посетить музей, на улице дождь'),[place(),place('node/2',kind='museum')])
        self.assertEqual([p['kind'] for p in results],['museum'])
    def test_work_does_not_promise_sockets(self):
        results,intent=app.retrieve(dict(BASE,query='Кофе и розетка'),[place(kind='cafe')])
        self.assertEqual(intent,'work');self.assertIn('не подтверждены',results[0]['why'])
    def test_return_trip_budget(self):
        results,_=app.retrieve(dict(BASE,minutes=10),[place()])
        self.assertEqual(results,[])
    def test_invalid_coordinates(self):
        with self.assertRaises(ValueError):app.retrieve(dict(BASE,lat=float('nan')),[])
    def test_duplicate_venue(self):
        results,_=app.retrieve(BASE,[place(name='Парк'),place('node/2',name='Парк')])
        self.assertEqual(len(results),1)
    def test_api_failure_falls_back_honestly(self):
        with patch.object(app,'KEY','mock'),patch.object(app,'ai_profile',side_effect=ValueError('offline test')),patch.object(app,'retrieve',return_value=([place()], 'walk')),patch.object(app,'ai_ideas',side_effect=RuntimeError('Лимит')):
            r=app.recommend(dict(BASE,use_ai=True))
            self.assertEqual(r['mode'],'template'); self.assertIn('резервный режим',r['note'])
    def test_no_key_does_not_claim_generation(self):
        with patch.object(app,'KEY',''),patch.object(app,'retrieve',return_value=([], 'walk')):
            r=app.recommend(dict(BASE,use_ai=True))
            self.assertEqual(r['mode'],'template');self.assertIn('Ключ',r['note'])
    def test_unknown_ai_ids_rejected(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self):return b'{"choices":[{"message":{"content":"{\\"ideas\\":[{\\"id\\":\\"invented\\",\\"action\\":\\"bad\\"}]}"}}]}'
        with patch.object(app.urllib.request,'urlopen',return_value=Response()):
            with self.assertRaises(RuntimeError):app.ai_ideas([place()],'walk')
class LanguageTests(unittest.TestCase):
    def setUp(self):
        # These unit tests isolate language/intent behavior; provider gating has its own tests.
        gate=patch.object(app,'verification_gate',side_effect=lambda candidates,profile:(candidates,'checked'))
        gate.start();self.addCleanup(gate.stop)
    def test_intents_in_three_languages(self):
        for query,intent in [('Хочу кофе','work'),('Кофе мен ноутбукке арналған розетка іздеймін','work'),('Coffee with my laptop','work'),('Баламмен саябақ іздеймін','family'),('With my child','family'),('Мұражайға барғым келеді','culture'),('Visit a museum','culture')]:
            with self.subTest(query=query):
                self.assertEqual(app.retrieve(dict(BASE,query=query),[])[1],intent)
    def test_localized_template_responses(self):
        for lang,category,opening in [('ru','Парк','Открытие'),('kk','Саябақ','Қазір'),('en','Park','Current')]:
            with self.subTest(lang=lang),patch.object(app,'dataset',return_value={'places':[place()]}):
                r=app.recommend(dict(BASE,lang=lang))
                self.assertEqual(r['lang'],lang)
                self.assertEqual(r['items'][0]['category'],category)
                self.assertTrue(r['items'][0]['hours_status'].startswith(opening))
                self.assertNotEqual(r['items'][0]['action'],'')
    def test_source_language_names(self):
        with patch.object(app,'dataset',return_value={'places':[place(names={'kk':'Саябақ атауы','en':'Park name'})]}):
            self.assertEqual(app.recommend(dict(BASE,lang='kk'))['items'][0]['name'],'Саябақ атауы')
    def test_invalid_language(self):
        with self.assertRaises(ValueError): app.recommend(dict(BASE,lang='invalid'))
    def test_gemini_requested_language(self):
        with patch.object(app,'KEY','mock'),patch.object(app,'ai_profile',side_effect=ValueError('offline test')),patch.object(app,'ai_ideas',return_value={'node/1':'An activity'} ) as generate,patch.object(app,'dataset',return_value={'places':[place()]}):
            r=app.recommend(dict(BASE,lang='en',use_ai=True))
            self.assertEqual(generate.call_args[0][2],'en')
            self.assertEqual(r['mode'],'gemini')
    def test_no_museums_in_english_and_kazakh(self):
        for query in ('A walk without museums','Мұражайсыз серуен'):
            rows,_=app.retrieve(dict(BASE,query=query),[place(kind='museum')])
            self.assertEqual(rows,[])
class UnderstandingTests(unittest.TestCase):
    def setUp(self):
        # These unit tests isolate language/intent behavior; provider gating has its own tests.
        gate=patch.object(app,'verification_gate',side_effect=lambda candidates,profile:(candidates,'checked'))
        gate.start();self.addCleanup(gate.stop)
    def test_explicitly_closed_places_excluded(self):
        rows,_=app.retrieve(dict(BASE,query='Хочу поесть'),[place(kind='restaurant',hours='closed')])
        self.assertEqual(rows,[])
    def test_food_overrides_stale_scenario(self):
        data=dict(BASE,query='Я голодная, хочу поесть',intent='work')
        rows,_=app.retrieve(data,[place(kind='restaurant'),place('node/2',kind='park')])
        self.assertEqual([p['kind'] for p in rows],['restaurant'])
    def test_coffee_is_not_necessarily_laptop_work(self):
        rows,_=app.retrieve(dict(BASE,query='Просто хочу выпить кофе'),[place(kind='cafe')])
        self.assertNotIn('ноутбук',rows[0]['why'])
        self.assertNotIn('работать',rows[0]['action'])
    def test_quiet_rest_is_not_automatically_a_cafe(self):
        p=local_profile('Хочу посидеть в тишине и отдохнуть')
        self.assertNotIn('cafe',p['include'])
        self.assertIn('park',p['include'])
    def test_negated_coffee_is_not_positive(self):
        p=local_profile('Не хочу кофе, хочу погулять')
        self.assertIn('cafe',p['exclude'])
        self.assertNotIn('cafe',p['include'])
    def test_eating_with_child(self):
        for query in ('С ребёнком хочу пообедать','Баламмен тамақ ішкім келеді','I am hungry with my child'):
            self.assertIn('restaurant',local_profile(query)['include'])
    def test_total_time_in_request(self):
        rows,_=app.retrieve(dict(BASE,query='У меня только 20 минут, хочу парк'),[place()])
        self.assertEqual(rows,[])  # 20 min visit + return trip exceeds 20 min.
    def test_max_walk_in_request(self):
        rows,_=app.retrieve(dict(BASE,query='Парк не дальше 5 минут пешком'),[place(lon=71.438)])
        self.assertEqual(rows,[])
    def test_no_outdoor_when_user_refuses_street(self):
        rows,_=app.retrieve(dict(BASE,query='Не хочу на улицу, хочу музей'),[place(),place('node/2',kind='museum')])
        self.assertEqual([r['kind'] for r in rows],['museum'])
    def test_cinema_not_replaced_with_park(self):
        with patch.object(app,'KEY',''),patch.object(app,'dataset',return_value={'places':[place()]}):
            r=app.recommend(dict(BASE,query='Хочу в кино'))
            self.assertEqual(r['items'],[])
            self.assertFalse(local_profile('Хочу в кино')['unsupported'])
    def test_semantic_schema_rejects_unknown_categories(self):
        with self.assertRaises(ValueError): clean_profile({'include':['secret_rooftop']})
        with self.assertRaises(ValueError): clean_profile({'max_minutes':float('inf')})
    def test_semantic_limits_do_not_relax_explicit_limits(self):
        p=merge_profiles(local_profile('Есть только 30 минут без музеев'),clean_profile({'include':['museum','park'],'max_minutes':120}))
        self.assertEqual(p['max_minutes'],30)
        self.assertIn('museum',p['exclude'])
    def test_semantic_interpretation_is_applied_before_retrieval(self):
        p=clean_profile({'include':['restaurant'],'summary':'Хочу перекусить','unsupported':False})
        with patch.object(app,'KEY','mock'),patch.object(app,'ai_profile',return_value=p),patch.object(app,'ai_ideas',return_value={'node/1':'Уточните меню.'}),patch.object(app,'dataset',return_value={'places':[place(kind='restaurant')]}):
            r=app.recommend(dict(BASE,query='Желудок урчит, спасайте',use_ai=True))
            self.assertEqual(r['understanding_mode'],'semantic')
            self.assertEqual(r['items'][0]['kind'],'restaurant')
            self.assertEqual(r['understanding'],'Хочу перекусить')
            self.assertFalse(app.AI_LOCK.locked())
    def test_parser_failure_is_disclosed(self):
        with patch.object(app,'KEY','mock'),patch.object(app,'ai_profile',side_effect=ValueError('bad schema')),patch.object(app,'ai_ideas',return_value={'node/1':'Идея'}),patch.object(app,'dataset',return_value={'places':[place()]}):
            r=app.recommend(dict(BASE,use_ai=True))
            self.assertEqual(r['understanding_mode'],'local')
            self.assertFalse(app.AI_LOCK.locked())
class FoodEvidenceTests(unittest.TestCase):
    def setUp(self):
        # These unit tests isolate language/intent behavior; provider gating has its own tests.
        gate=patch.object(app,'verification_gate',side_effect=lambda candidates,profile:(candidates,'checked'))
        gate.start();self.addCleanup(gate.stop)
    def test_specific_dish_without_evidence_is_not_recommended(self):
        rows,_=app.retrieve(dict(BASE,query='Хочу поесть суши'),[place(kind='restaurant')])
        self.assertEqual(rows,[])
    def test_japanese_does_not_prove_sushi(self):
        rows,_=app.retrieve(dict(BASE,query='Хочу суши'),[place(kind='restaurant',food_tags={'cuisine':'japanese'})])
        self.assertEqual(rows,[])
    def test_italian_does_not_prove_carbonara(self):
        rows,_=app.retrieve(dict(BASE,query='Хочу карбонару'),[place(kind='restaurant',food_tags={'cuisine':'italian'})])
        self.assertEqual(rows,[])
    def test_name_and_description_are_not_menu_evidence(self):
        rows,_=app.retrieve(dict(BASE,query='Хочу плов'),[place(kind='restaurant',name='Центр плова',description='ИИ сказал, что тут есть плов')])
        self.assertEqual(rows,[])
    def test_exact_source_specialization_and_proof(self):
        rows,_=app.retrieve(dict(BASE,query='Хочу суши'),[place(kind='restaurant',food_tags={'cuisine':'pizza;sushi'})])
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['food_evidence'][0]['value'],'pizza;sushi')
        self.assertEqual(rows[0]['food_evidence'][0]['provider'],'OpenStreetMap')
    def test_kazakh_and_english_food(self):
        for query in ('Суши жегім келеді','I want sushi'):
            rows,_=app.retrieve(dict(BASE,query=query),[place(kind='restaurant')])
            self.assertEqual(rows,[])
    def test_diet_requires_its_own_source_tag(self):
        for query in ('Хочу халяль еду','I want vegan food'):
            rows,_=app.retrieve(dict(BASE,query=query),[place(kind='restaurant',food_tags={'cuisine':'turkish'})])
            self.assertEqual(rows,[])
        rows,_=app.retrieve(dict(BASE,query='Хочу халяль еду'),[place(kind='restaurant',food_tags={'diet:halal':'yes'})])
        self.assertEqual(len(rows),1)
    def test_allergy_not_proven_by_cuisine_or_diet(self):
        rows,_=app.retrieve(dict(BASE,query='Хочу поесть без арахиса, аллергия'),[place(kind='restaurant',food_tags={'diet:vegan':'yes'})])
        self.assertEqual(rows,[])
    def test_unknown_food_fails_closed(self):
        rows,_=app.retrieve(dict(BASE,query='Хочу поесть кордон блю'),[place(kind='restaurant')])
        self.assertEqual(rows,[])
    def test_model_cannot_weaken_dish_to_cuisine(self):
        p=merge_profiles(local_profile('Хочу карбонару'),clean_profile({'include':['restaurant'],'food_requirements':[{'type':'cuisine','value':'italian'}]}))
        rows,_=app.retrieve(dict(BASE,query='Хочу карбонару',_profile=p),[place(kind='restaurant',food_tags={'cuisine':'italian'})])
        self.assertEqual(rows,[])
    def test_generator_cannot_insert_menu_claim(self):
        profile=clean_profile({'include':['restaurant'],'summary':'Хочу поесть','unsupported':False})
        with patch.object(app,'KEY','mock'),patch.object(app,'ai_profile',return_value=profile),patch.object(app,'ai_ideas',return_value={'node/1':'Здесь есть карбонара и суши.'}),patch.object(app,'dataset',return_value={'places':[place(kind='restaurant')]}):
            r=app.recommend(dict(BASE,query='Хочу поесть',use_ai=True))
            self.assertFalse(r['items'][0]['generated'])
            self.assertNotIn('карбонара',r['items'][0]['action'])
    def test_no_food_records_sent_to_idea_generator(self):
        with patch.object(app,'gemini_json') as provider:
            self.assertEqual(app.ai_ideas([place(kind='restaurant')],'Хочу поесть'),{})
            provider.assert_not_called()
    def test_no_match_explained_in_all_languages(self):
        for lang in ('ru','kk','en'):
            with patch.object(app,'dataset',return_value={'places':[place(kind='restaurant')]}):
                r=app.recommend(dict(BASE,query='Хочу карбонару',lang=lang))
                self.assertEqual(r['items'],[])
                self.assertTrue(r['empty'])
class SourceTests(unittest.TestCase):
    def test_source_urls_are_branch_specific_and_safe(self):
        from sources import safe_source_url
        self.assertTrue(safe_source_url('https://2gis.kz/astana/firm/70000001046956645'))
        for url in ('https://2gis.kz/astana/search/food','http://127.0.0.1:8765','https://2gis.kz.evil.com/astana/firm/1','javascript:alert(1)','https://2gis.kz@evil.com/astana/firm/1'):
            self.assertFalse(safe_source_url(url))
    def test_invalid_ratings_not_displayed(self):
        from sources import valid_source
        for rating in (10,'4.9',True,float('nan')):
            result=valid_source({'url':'https://2gis.kz/astana/firm/123','rating':rating})
            self.assertNotIn('rating',result)
    def test_old_snapshot_is_no_longer_used(self):
        from sources import enrich_places
        rows=enrich_places([place('node/14100100183',name='Peek-a-boo')])
        self.assertEqual(rows[0]['external_sources'],[])
    def test_external_source_can_prove_korean_cuisine(self):
        from sources import enrich_places
        record=place(kind='restaurant',external_sources=[{'provider':'2ГИС','url':'https://2gis.kz/astana/firm/123',
            'mode':'api','facts':[{'type':'cuisine','value':'korean'}]}])
        result,_=app.retrieve(dict(BASE,query='Хочу корейскую еду'),enrich_places([record]))
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['food_evidence'][0]['provider'],'2ГИС')
    def test_asian_does_not_prove_korean(self):
        result,_=app.retrieve(dict(BASE,query='Хочу корейскую еду'),[place(kind='restaurant',food_tags={'cuisine':'asian'})])
        self.assertEqual(result,[])
    def test_misspelled_korean_is_still_strict(self):
        result,_=app.retrieve(dict(BASE,query='хочу корескую еду'),[place(kind='restaurant')])
        self.assertEqual(result,[])
    def test_model_search_report_cannot_supply_rating_evidence(self):
        from sources import web_discovery
        profile=local_profile('Хочу корейскую еду')
        def complete(payload):
            self.assertEqual(payload['tools'],[{'type':'browser_search'}])
            self.assertEqual(payload['tool_choice'],'required')
            self.assertNotIn('response_format',payload)
            self.assertNotIn('lat',payload['messages'][1]['content'])
            return {'choices':[{'message':{'content':'Fake ★5.0 https://2gis.kz/astana/firm/123'}}]}
        report=web_discovery('private request',profile,[],complete)
        self.assertFalse(report['verified'])
        self.assertFalse(report['used_for_ratings'])
        self.assertFalse(report['used_for_matching'])
    def test_live_provider_uses_attributes_not_query_for_cuisine(self):
        from sources import normalize_2gis_item
        raw={'id':'123','name':'Cafe','point':{'lat':51.1282,'lon':71.4304},'reviews':{'general_rating':4.6,'general_review_count':20},'attribute_groups':[{'attributes':[{'name':'Корейская кухня','tag':'food_service_korean'}]}]}
        p=normalize_2gis_item(raw,'2026-10-17')
        self.assertEqual(p['external_sources'][0]['rating'],4.6)
        rows,_=app.retrieve(dict(BASE,query='Хочу корейскую еду'),[p])
        self.assertEqual(len(rows),1)
        raw['attribute_groups']=[]
        p=normalize_2gis_item(raw,'2026-10-17')
        rows,_=app.retrieve(dict(BASE,query='Хочу корейскую еду'),[p])
        self.assertEqual(rows,[])
    def test_organisation_rating_not_relabelled_branch_rating(self):
        from sources import normalize_2gis_item
        p=normalize_2gis_item({'id':'123','name':'Cafe','point':{'lat':51.1,'lon':71.4},'reviews':{'general_rating':5,'is_org_reviews':True}},'2026-10-17')
        self.assertNotIn('rating',p['external_sources'][0])
if __name__=='__main__': unittest.main()
