#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bounded, repeatable official 2GIS API collection. No embedded credentials."""
import argparse,datetime,getpass,hashlib,json,pathlib,threading,time,urllib.parse
from sources import provider_json,normalize_2gis_item,LIVE_FIELDS
from catalog import build
from categories import EXTRA
ROOT=pathlib.Path(__file__).resolve().parent
QUERIES=('кафе','рестораны','кофейни','суши','корейская кухня','пиццерии',
         'столовые','пекарни','кондитерские','бургерные','казахская кухня',
         'итальянская кухня','грузинская кухня','китайская кухня','вегетарианские кафе',
         'музеи','галереи','парки','скверы','библиотеки','смотровые площадки',
         'достопримечательности','детские площадки','театры','кинотеатры',
         'выставочные центры','ботанические сады','развлекательные центры','ночные клубы','караоке','боулинг')
QUERIES=tuple(dict.fromkeys(QUERIES+tuple(value[0] for value in EXTRA.values())))
LOCK=threading.Lock()
STATE={'status':'idle','count':0}

def collect(key,pages=50,contacts=False,max_requests=600):
    if not 1<=pages<=1000 or not 1<=max_requests<=5000:raise ValueError("Invalid collection limits")
    if not LOCK.acquire(blocking=False):return dict(STATE)
    STATE.update(status='collecting',count=0)
    try:
        now=datetime.datetime.now(datetime.timezone.utc).isoformat()
        places={};requests=[];raw_pages=[];stops={};request_count=0
        fields=LIVE_FIELDS+(',items.contact_groups' if contacts else '')
        # Round-robin pages: the request budget covers every category before deeper pages.
        active={query:set() for query in QUERIES}
        for page in range(1,pages+1):
            for query in QUERIES:
                if query not in active:continue
                if request_count>=max_requests:
                    stops[query]='request_budget';continue
                params={'q':'Астана '+query,'key':key,'page':page,'page_size':10,
                        'fields':fields,'locale':'ru_KZ'}
                request_count+=1
                raw=provider_json('https://catalog.api.2gis.com/3.0/items?'+urllib.parse.urlencode(params))
                code=raw.get('meta',{}).get('code')
                if code==404:
                    stops[query]='no_more_results';active.pop(query);continue
                if code!=200:raise ValueError('Provider rejected collection')
                items=raw.get('result',{}).get('items',[])
                requests.append({'query':query,'page':page,'received':len(items),
                                 'reported_total':raw.get('result',{}).get('total')})
                raw_pages.append({'query':query,'page':page,'items':items})
                for item in items:
                    place=normalize_2gis_item(item,now)
                    if place:places[place['id']]=place
                STATE['count']=len(places)
                ids={str(item.get('id')) for item in items if item.get('id')}
                total=raw.get('result',{}).get('total')
                if not ids or not ids-active[query]:
                    stops[query]='no_new_ids';active.pop(query)
                elif len(items)<10 or (isinstance(total,int) and page*10>=total):
                    stops[query]='end_of_results';active.pop(query)
                else:active[query].update(ids)
                STATE.update(requests=request_count,query=query,page=page)
                time.sleep(.15)
            if not active or request_count>=max_requests:break
        for query in active:stops.setdefault(query,'request_budget' if request_count>=max_requests else 'page_limit')
        if not places:raise ValueError('No valid places; previous provider database retained')
        metadata={'source':'2ГИС','collected_at':now,'coverage':'Астана; категории и страницы, указанные в журнале',
                  'complete_city':False,'method':'Official Places API; pagination; branch-ID deduplication; closure and coordinate filtering',
                  'queries':list(QUERIES),'pages_per_query_limit':pages,'requests':requests,
                  'request_budget':max_requests,'requests_used':request_count,'stop_reasons':stops,
                  'missing_values':'Source did not provide field or key lacks permission'}
        result=build(places.values(),metadata)
        data=ROOT/'data'
        # Contains API item data only, never request URLs, credentials or user coordinates.
        payload=json.dumps(raw_pages,ensure_ascii=False).encode('utf8')
        result['raw_sha256']=hashlib.sha256(payload).hexdigest()
        (data/'2gis-collected.json').write_text(json.dumps({'metadata':result,'places':list(places.values())},ensure_ascii=False,indent=2),encoding='utf8')
        (data/'2gis-raw.json').write_bytes(payload)
        (data/'catalog-info.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
        STATE.update(status='ready',count=len(places))
        return result
    except Exception:
        STATE.update(status='failed')
        raise
    finally:LOCK.release()

def start_collection(key):
    def worker():
        try:collect(key)
        except Exception:pass # Status exposed without credential-bearing error details.
    threading.Thread(target=worker,daemon=True).start()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Сбор датасета Астаны из 2ГИС')
    parser.add_argument('--pages',type=int,default=50)
    parser.add_argument('--max-requests',type=int,default=600)
    parser.add_argument('--contacts',action='store_true',help='Только если ключ имеет доступ к контактам')
    args=parser.parse_args()
    if not 1<=args.pages<=1000 or not 1<=args.max_requests<=5000:parser.error('Страницы: 1–1000; бюджет запросов: 1–5000')
    try:
        result=collect(getpass.getpass('Ключ 2ГИС (ввод скрыт): ').strip(),args.pages,args.contacts,args.max_requests)
        print('Собрано мест:',result['count'])
    except Exception:
        print('Сбор не завершён. Проверьте ключ, доступ к Places API и интернет. Старая база не подменяется.')
        raise SystemExit(1)
