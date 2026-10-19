# -*- coding: utf-8 -*-
"""Bounded request understanding. No coordinates or credentials in profiles."""
import math,re
from categories import EXTRA,WALKING,PARK_PATTERN,GARDEN_PATTERN,KINDERGARTEN_PATTERN
from food_rules import food_request, clean_requirements, needs_specific_food_check
KINDS={'cinema','nightclub','karaoke','bowling','cafe','restaurant','library','arts_centre','museum','attraction','viewpoint','gallery','park','playground','garden'}
OUTSIDE={'park','playground','garden','viewpoint','attraction'}
PATTERNS={
 'cinema':r'кино|cinema|movies?|кинотеатр',
 'nightclub':r'ночн\w*\s+клуб|\bnightclub\b|\bclub\b|түнгі\s+клуб|потанцев|танцы',
 'karaoke':r'караоке|karaoke',
 'bowling':r'боулинг|bowling',
 'cafe':r'коф[ею]|кофейн|капучино|латте|эспрессо|американо|кафе|coffee|cappuccino|latte|espresso|café|\bcafe\b|кофехана',
 'restaurant':r'поесть|покуш|голод|обед|ужин|завтрак|ресторан|ед[аы]\b|хочу\s+еду|eat\b|food|hungry|lunch|dinner|breakfast|restaurant|тамақ|қарным|мейрамхана',
 'park':PARK_PATTERN,
 'garden':GARDEN_PATTERN,
 'playground':r'детск\w*\s+площад|playground|балалар\s+алаң',
 'museum':r'музе|museum|мұражай',
 'gallery':r'галере|gallery|galleries',
 'library':r'библиотек|library|кітапхана',
 'viewpoint':r'смотров|viewpoint|панорам|көрініс\s+алаң',
 'arts_centre':r'культур|culture|мәдениет',
}

OUTSIDE.update(WALKING)
KINDS.update(EXTRA)
PATTERNS.update({key:value[1] for key,value in EXTRA.items()})

def finite_number(value,low,high):
    if isinstance(value,bool) or not isinstance(value,(float,int)): return None
    return value if math.isfinite(value) and low<=value<=high else None

def clean_profile(raw):
    """Reject untrusted model schema; do not allow generated code/coordinates."""
    if not isinstance(raw,dict): raise ValueError('Invalid profile')
    p={}
    for field in ('include','exclude'):
        values=raw.get(field,[])
        if not isinstance(values,list) or any(not isinstance(v,str) or v not in KINDS for v in values):
            raise ValueError('Unknown category')
        p[field]=list(dict.fromkeys(values))
    for field in ('indoors','outdoors','wheelchair','unsupported','needs_clarification'):
        if not isinstance(raw.get(field,False),bool): raise ValueError('Invalid flag')
        p[field]=raw.get(field,False)
    for field,low,high in [('max_minutes',1,math.inf),('max_walk_minutes',1,math.inf),('max_distance_m',100,100000)]:
        value=raw.get(field)
        if value is not None and finite_number(value,low,high) is None: raise ValueError('Invalid limit')
        p[field]=value
    p['food_requirements']=clean_requirements(raw.get('food_requirements',[]))
    if not isinstance(raw.get('food_unverified',False),bool): raise ValueError('Invalid food flag')
    p['food_unverified']=raw.get('food_unverified',False)
    p['summary']=str(raw.get('summary',''))[:300]
    p['clarification']=str(raw.get('clarification',''))[:300]
    p['unverified']=[v for v in raw.get('unverified',[]) if isinstance(v,str) and v in ('sockets','quiet','free','children','hours')][:5] if isinstance(raw.get('unverified',[]),list) else []
    if p['indoors'] and p['outdoors']: raise ValueError('Conflicting environment')
    return p

def local_profile(query):
    q=query.lower().replace('ё','е')
    kindergarten_requested=bool(re.search(KINDERGARTEN_PATTERN,q,re.I))
    q=re.sub(KINDERGARTEN_PATTERN,' ',q,flags=re.I)
    p=clean_profile({})
    positive=[];excluded=[]
    # Strip negated category phrases before classification: "не хочу кофе" is not work.
    for kind,pattern in PATTERNS.items():
        neg=r'(?:без|кроме|не\s+хочу|не\s+надо|не\s+предлагай|no|without|not|except)\s+(?:\w+\s+){0,2}?(?:'+pattern+r')\w*'
        suffix=r'(?:'+pattern+r')\w*\s+(?:емес|керек\s+емес|жоқ)'
        if re.search(neg,q) or re.search(suffix,q) or (kind=='museum' and 'мұражайсыз' in q) or (kind=='cafe' and ('кофесіз' in q or 'кафесіз' in q)):
            excluded.append(kind);q=re.sub(neg,' ',q);q=re.sub(suffix,' ',q)
        elif re.search(pattern,q): positive.append(kind)
    if 'waterpark' in positive:positive=[kind for kind in positive if kind not in ('park','garden')]
    if 'cinema' in positive:positive=[kind for kind in positive if kind!='theatre']
    p['exclude']=excluded
    if not positive and re.search(r'ноч|\bnight\b|түн',q) and not re.search(r'прогуля|погуля|прогул|серуен|\bwalk\b',q):positive=['nightclub','cinema','karaoke','bowling']
    working=bool(re.search(r'поработ|работа|ноутбук|розет|laptop|\bwork\b|socket|жұмыс|ноутбук',q))
    family=bool(re.search(r'\bребен|\bдет(?:и|ь|ск)|\bchild|\bkids?\b|\bfamily|\bбала|отбас',q))
    if positive:p['include']=positive
    elif working:p['include']=['cafe','library']
    elif family:p['include']=['park','playground','museum','garden']
    elif re.search(r'тих|спокой|отдох|почита|quiet|relax|read|тыныш|демал|кітап',q):p['include']=['park','garden','library']
    else:p['include']=['park','garden','attraction','viewpoint','gallery','museum']
    p['walking_only']=not positive and bool(re.search(r'прогуля|погуля|серуен|\bwalk\b',q))
    if p['walking_only']:p['include']=['park','garden','attraction','viewpoint']
    p['indoors']=bool(re.search(r'в\s+помещен|дожд|indoor|rain|жаңбыр|жабық\s+орын|на\s+улиц\w*\s+не\s+хочу|не\s+на\s+улиц|не\s+хочу\s+на\s+улиц',q))
    p['outdoors']=not p['indoors'] and bool(re.search(r'на\s+улиц|свеж\w*\s+воздух|outdoor|outside|таза\s+ауа|далада',q))
    p['wheelchair']=bool(re.search(r'инвалид|безбарьер|wheelchair|арбамен|арбаға',q))
    for name,pattern in [('sockets',r'розет|socket|power outlet'),('quiet',r'тих|тишин|quiet|тыныш'),('free',r'бесплат|\bfree\b|тегін'),('children',r'ребен|child|балам|балалар')]:
        if re.search(pattern,q):p['unverified'].append(name)
    # Interpret explicit duration and walking-distance constraints; do not enlarge form limits.
    minutes=re.search(r'(\d{1,3})\s*(?:минут\w*|мин\b|minutes?\b|mins?\b)',q)
    hours=re.search(r'(\d{1,3}(?:[.,]\d)?)\s*(?:час\w*|hours?\b|сағат)',q)
    if re.search(r'пар[ау]\s+час|два\s+час|couple of hours|екі сағат',q):p['max_minutes']=120
    elif re.search(r'три\s+час|three hours|үш сағат',q):p['max_minutes']=180
    elif 'полчас' in q or 'half an hour' in q or 'жарты сағат' in q:p['max_minutes']=30
    elif re.search(r'(?:на|есть|меня|менде)\s+(?:один\s+)?час\b|one hour|бір сағат',q):p['max_minutes']=60
    elif hours:p['max_minutes']=finite_number(float(hours[1].replace(',','.'))*60,1,math.inf)
    elif minutes and not re.search(r'пешком|walk|жаяу',q[max(0,minutes.start()-20):minutes.end()+20]):p['max_minutes']=finite_number(int(minutes[1]),1,math.inf)
    walking=re.search(r'(\d{1,3})\s*(?:минут\w*|мин\b|minutes?\b|mins?\b)\s*(?:пешком|walk|жаяу)',q)
    if walking:p['max_walk_minutes']=finite_number(int(walking[1]),1,120)
    metres=re.search(r'(\d{2,5})\s*(?:метр\w*|м\b|meters?\b|metres?\b)',q)
    km=re.search(r'(\d(?:[.,]\d+)?)\s*(?:км|km)\b',q)
    if metres:p['max_distance_m']=finite_number(int(metres[1]),100,10000)
    elif km:p['max_distance_m']=finite_number(float(km[1].replace(',','.'))*1000,100,10000)
    elif re.search(r'рядом|недалеко|поблизости|ближе|ближайш|\bnear(?:by|est)?\b|жақын',q) and not re.search(r'не\s+рядом|not\s+near',q):p['max_distance_m']=1000
    unsupported=bool(re.search(r'дәріхана|аптек|pharmacy',q))
    p['unsupported']=(unsupported or kindergarten_requested) and not positive
    if kindergarten_requested and not positive:p['include']=[]
    p['food_requirements'],p['food_unverified']=food_request(query)
    p['food_unknown_local']=not p['food_requirements'] and needs_specific_food_check(query)
    if p['food_requirements'] or p['food_unverified']:
        p['include']=['restaurant','cafe']
    if not positive and not working and not family and re.search(r'что.?то|что.?нибудь|не знаю|чем заняться|something|бірдеңе',q) and not p.get('walking_only'):
        p['needs_clarification']=True
        p['clarification']='Какой отдых вам ближе: спокойная прогулка, культура, еда или активные развлечения?'
    walking=bool(re.search(r'прогуля|погуля|прогул|серуен|\bwalk\b',q))
    p['walking_requested']=walking
    if walking and not p['food_requirements']:
        nature=bool(re.search(r'зелень|зелен|природ|тих|тишин|nature|green|quiet|тыныш',q))
        urban=bool(re.search(r'архитектур|architecture|сәулет',q))
        lively=bool(re.search(r'оживлен|людн|lively|busy|жанды|пешеход|pedestrian|жаяу',q))
        if urban:p['include']=['architecture','square','boulevard','pedestrian','attraction','viewpoint']
        elif lively:p['include']=['pedestrian']
        elif nature and not positive:p['include']=['park','garden','promenade']
        elif not positive:p['include']=['promenade','boulevard','square','pedestrian','architecture','park','garden','attraction','viewpoint']
        if 'cafe' in positive and len(positive)==1:p['include']=['promenade','boulevard','pedestrian','cafe']
        if not positive and not (nature or urban or lively):
            p['needs_clarification']=True
            p['clarification']='Какая прогулка вам ближе: зелень и тишина или городская архитектура?'
        else:p['needs_clarification']=False;p['clarification']=''
    p['time_unlimited']=bool(re.search(r'неогранич|много\s+времени|времени\s+много|никуда\s+не\s+(?:спешу|тороплюсь)|без\s+ограничен.*времен|времени\s+сколько\s+угодно|время\s+не\s+огранич|без\s+спешки|unlimited\s+time|no\s+time\s+limit|уақыт.*шектеусіз',q))
    if p['time_unlimited']:p['max_minutes']=None
    p['radius_unlimited']=bool(re.search(r'не\s*важно\s+где|где\s+угодно|любой\s+радиус|расстояни\w*\s+не\s*важ|по\s+всей\s+астане|anywhere|any\s+distance|қашықтық.*маңызды\s+емес',q))
    if p['radius_unlimited']:p['max_distance_m']=None
    p['family_dining']=bool(re.search(r'семейн\w*\s+(?:кафе|ресторан)|family[ -](?:friendly[ -])?(?:cafe|café|restaurant)|отбасылық\s+(?:кафе|мейрамхана)',q))
    if p['family_dining']:p['include']=[k for k in p['include'] if k in ('cafe','restaurant')] or ['cafe','restaurant']
    p['coffee_venues_only']='cafe' in positive and 'restaurant' not in positive and not p['food_requirements'] and not p['food_unverified']
    p['working']=working
    return p

def merge_profiles(local,semantic):
    """Semantic categories enrich recall; explicit negatives and hard limits survive."""
    result=dict(semantic)
    result['exclude']=sorted(set(local['exclude'])|set(semantic['exclude']))
    for flag in ('wheelchair',):result[flag]=local[flag] or semantic[flag]
    for field in ('max_minutes','max_walk_minutes','max_distance_m'):
        limits=[p[field] for p in (local,semantic) if p[field] is not None]
        result[field]=min(limits) if limits else None
    result['unverified']=sorted(set(local['unverified'])|set(semantic['unverified']))
    result['food_requirements']=clean_requirements(local.get('food_requirements',[])+semantic.get('food_requirements',[]))
    result['food_unverified']=local.get('food_unverified',False) or local.get('food_unknown_local',False) or semantic.get('food_unverified',False)
    if result['food_requirements'] or result['food_unverified']:result['include']=['restaurant','cafe']
    if local.get('walking_only') and not result['food_requirements']:
        result['include']=[k for k in result['include'] if k in ('park','garden','attraction','viewpoint')] or local['include']
    result['needs_clarification']=local.get('needs_clarification',False) or semantic.get('needs_clarification',False)
    if result['needs_clarification'] and not result.get('clarification'):result['clarification']=local.get('clarification','')
    if local.get('walking_requested'):
        result['walking_requested']=True
        result['include']=local['include']
        result['needs_clarification']=local['needs_clarification']
        result['clarification']=local['clarification']
    result['time_unlimited']=local.get('time_unlimited',False)
    if result['time_unlimited']:result['max_minutes']=None
    result['radius_unlimited']=local.get('radius_unlimited',False)
    if result['radius_unlimited']:result['max_distance_m']=None
    result['family_dining']=local.get('family_dining',False)
    if result['family_dining']:result['include']=local['include']
    result['coffee_venues_only']=local.get('coffee_venues_only',False) and not result['food_requirements'] and not result['food_unverified']
    if result['coffee_venues_only']:result['include']=local['include']
    result['working']=local.get('working',False)
    return result


def clean_semantic_profile(raw):
    """Normalize harmless JSON representation differences, then run strict validation."""
    if not isinstance(raw,dict):raise ValueError('Invalid profile')
    value=dict(raw)
    for field in ('include','exclude','food_requirements','unverified'):
        if value.get(field,'missing') is None:value[field]=[]
    for field in ('indoors','outdoors','wheelchair','unsupported','needs_clarification','food_unverified'):
        if value.get(field,'missing') is None:value[field]=False
        if isinstance(value.get(field),str):
            flag=value[field].strip().lower()
            if flag in ('true','false'):value[field]=(flag=='true')
    for field in ('max_minutes','max_walk_minutes','max_distance_m'):
        item=value.get(field)
        if isinstance(item,str):
            text=item.strip().lower()
            if text in ('','null','none','unlimited','no limit'):value[field]=None
            else:
                try:value[field]=float(text.replace(',','.'))
                except ValueError:pass
        if value.get(field) == 0 and not isinstance(value.get(field),bool):value[field]=None
    return clean_profile(value)
