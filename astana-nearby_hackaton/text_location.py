# -*- coding: utf-8 -*-
"""Extract an explicitly stated starting point, then resolve it through 2GIS."""
import re,urllib.parse
from sources import provider_json

ALIASES=(
 (r'керу[еэ]н(?:а|е|ом)?\s*(?:сити|city)', 'KeruenCity'),
 (r'керу[еэ]н(?:а|е|ом)?', 'Keruen'),
 (r'мег(?:а|е|и|у|ой)\s+(?:силк|сильк)\s*(?:вей|вэй|уэй|way)', 'MEGA Silk Way'),
 (r'мег(?:а|е|и|у|ой)', 'MEGA'),
 (r'хан[ -]?шатыр(?:а|е)?', 'Хан Шатыр'),
 (r'байтерек(?:а|е)?|бәйтерек(?:а|е)?', 'Байтерек'),
 (r'экспо(?:\s+2017)?', 'EXPO'),
)

def name_variants(name):
    value=re.sub(r'^(?:трц|тц|торгов(?:ый|ого|ом)\s+центр(?:а|е)?)\s*', '',name.strip(),flags=re.I)
    value=value.strip(' «»"')
    for pattern,canonical in ALIASES:
        if re.fullmatch(pattern,value,re.I):return list(dict.fromkeys([canonical,value]))
    return [value]

def extract_start(query):
    text=str(query)[:700].strip()
    patterns=(r'(?:\b(?:я|мы)\s+(?:сейчас\s+)?(?:стою\s+|нахожусь\s+)?(?:у|около|возле|рядом\s+с|в|на)\s+)(.+)',
              r'(?:^|[,;]\s*)(?:сейчас\s+)?(?:нахожусь|стою)\s+(?:у|около|возле|рядом\s+с|в|на)\s+(.+)',
              r'^(?:сейчас\s+)?(?:у|около|возле|рядом\s+с)\s+(.+)',
              r'(?:\b(?:i\s*(?:am|’m|\x27m)|we\s+are)\s+(?:standing\s+)?(?:at|near|by|in)\s+)(.+)',
              r'\bмен\s+(.+?)(?:\s+жанында|\s+қасында|\s+алдында)(?:мын|мін)?')
    for pattern in patterns:
        match=re.search(pattern,text,re.I)
        if not match:continue
        start=re.split(r'[,;.!?]|\s+(?:и\s+)?(?:хочу|хотел|планирую|куда|want|would\s+like|looking|барғым)\b',match.group(1),maxsplit=1,flags=re.I)[0]
        start=re.sub(r'^(?:здании|здания|здание)\s+','',start,flags=re.I).strip(' «»"')
        if 2<=len(start)<=150:return start
    # Bare known landmark at the start is allowed, but a destination is not an origin.
    first=re.split(r'[,;.!?]',text,maxsplit=1)[0].strip(' «»"')
    for pattern,_ in ALIASES:
        if re.fullmatch(pattern,first,re.I):return first
    return None

def resolve_start(query,key):
    name=extract_start(query)
    if not name:return {'status':'missing'}
    if not key:return {'status':'no_key','query':name}
    params={'q':'Астана '+name_variants(name)[0],'key':key,'page_size':5,'fields':'items.point,items.name_ex,items.flags,items.dates','locale':'ru_KZ'}
    from sources import closed_provider_record
    try:
        raw=provider_json('https://catalog.api.2gis.com/3.0/items?'+urllib.parse.urlencode(params))
        if raw.get('meta',{}).get('code') not in (200,404):return {'status':'unavailable','query':name}
        if not raw.get('result',{}).get('items') and len(name_variants(name))>1:
            params['q']='Астана '+name_variants(name)[1]
            raw=provider_json('https://catalog.api.2gis.com/3.0/items?'+urllib.parse.urlencode(params))
            if raw.get('meta',{}).get('code') not in (200,404):return {'status':'unavailable','query':name}
        choices=[]
        for item in raw.get('result',{}).get('items',[]):
            point=item.get('point') or {};lat=point.get('lat');lon=point.get('lon')
            if closed_provider_record(item):continue
            if not isinstance(lat,(int,float)) or not isinstance(lon,(int,float)):continue
            if not (50.85<=lat<=51.36 and 71.21<=lon<=71.79):continue
            if any(abs(lat-c['lat'])<.0005 and abs(lon-c['lon'])<.0005 for c in choices):continue
            choices.append({'name':item.get('name',''),'address':item.get('address_name',''),'lat':lat,'lon':lon})
        if len(choices)==1:return dict(choices[0],status='resolved',query=name)
        return {'status':'ambiguous' if choices else 'not_found','query':name,'choices':choices}
    except Exception:return {'status':'unavailable','query':name}
