# -*- coding: utf-8 -*-
import pathlib,tempfile,unittest,urllib.parse
from unittest.mock import patch
import catalog,collect_2gis
from test_verification import raw

class PaginationTests(unittest.TestCase):
    def run_collector(self,provider,queries=('кафе',),budget=20):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory);(root/'data').mkdir()
            original=catalog.build
            with patch.object(collect_2gis,'ROOT',root),patch.object(collect_2gis,'QUERIES',queries),patch.object(collect_2gis,'provider_json',side_effect=provider),patch.object(collect_2gis.time,'sleep'),patch.object(collect_2gis,'build',side_effect=lambda rows,meta:original(rows,meta,root/'data/catalog.sqlite')):
                return collect_2gis.collect('fake-key',max_requests=budget)
    def test_continues_beyond_old_three_pages(self):
        def provider(url):
            page=int(urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)['page'][0])
            return {'meta':{'code':200},'result':{'total':45,'items':[raw(id=str(100000+page*10+i)) for i in range(5 if page==5 else 10)]}}
        result=self.run_collector(provider)
        self.assertEqual(result['count'],45);self.assertEqual(result['requests_used'],5)
        self.assertEqual(result['stop_reasons']['кафе'],'end_of_results')
    def test_repeated_page_stops(self):
        result=self.run_collector(lambda url:{'meta':{'code':200},'result':{'items':[raw(id=str(100000+i)) for i in range(10)],'total':999}})
        self.assertEqual(result['count'],10);self.assertEqual(result['requests_used'],2)
        self.assertEqual(result['stop_reasons']['кафе'],'no_new_ids')
    def test_budget_is_shared_across_categories(self):
        requested=[]
        def provider(url):
            params=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query);requested.append((params['q'][0],params['page'][0]))
            return {'meta':{'code':200},'result':{'items':[raw(id=str(100000+i)) for i in range(10)],'total':999}}
        result=self.run_collector(provider,('кафе','музеи'),2)
        self.assertEqual(requested,[('Астана кафе','1'),('Астана музеи','1')]);self.assertEqual(result['requests_used'],2)
        self.assertEqual(set(result['stop_reasons'].values()),{'request_budget'})

if __name__=='__main__':unittest.main()
