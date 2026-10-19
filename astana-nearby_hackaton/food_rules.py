# -*- coding: utf-8 -*-
"""Food preferences are constraints; only source tags are evidence, never LLM text."""
import re
from sources import cuisine_evidence
FOOD_KINDS={'cafe','restaurant'}
ALIASES={
 'pizza':r'пицц|пицц|\bpizza\b',
 'sushi':r'суши|суші|\bsushi\b',
 'burger':r'бургер|\bburgers?\b',
 'steak_house':r'стейк|\bsteaks?\b',
 'kebab':r'шашлык|шашлик|кәуап|шашлы|\bkebab\b',
 'ramen':r'рамен|рамэн|\bramen\b',
 'pasta':r'паст[ауы]|макарон|\bpasta\b',
 'carbonara':r'карбонар|\bcarbonara\b',
 'plov':r'\bплов|\bпалау|\bplov\b|\bpilaf\b',
 'lagman':r'лагман|лағман|\blagman\b',
 'beshbarmak':r'бешбармак|бесбармақ|\bbeshbarmak\b',
 'khachapuri':r'хачапури|\bkhachapuri\b',
 'khinkali':r'хинкал|\bkhinkali\b',
 'dumplings':r'пельмен|тұшпара|\bdumplings?\b',
 'manti':r'\bмант|\bмәнті|\bmanti\b',
 'soup':r'\bсуп\w*|\bsoup\b|\bсорпа',
 'borscht':r'борщ|\bborscht\b',
 'salad':r'салат|\bsalad\b',
 'seafood':r'морепродукт|теңіз\s+өнім|\bseafood\b',
 'chicken':r'куриц|тауық|\bchicken\b',
 'fish':r'\bрыб\w*|\bбалық|\bfish\b',
 'dessert':r'десерт|тәтті|\bdesserts?\b',
 'cake':r'\bторт|\bcake\b',
 'ice_cream':r'морожен|балмұздақ|\bice\s*cream\b',
}
CUISINES={
 'italian':r'итальян|италия|итальяндық|\bitalian\b',
 'japanese':r'япон|жапон|\bjapanese\b',
 'chinese':r'китай|қытай|\bchinese\b',
 'korean':r'корей|кореск|кәріс|\bkorean\b',
 'georgian':r'грузин|грузия|\bgeorgian\b',
 'kazakh':r'казахск|қазақ|\bkazakh\b',
 'turkish':r'турец|түрік|\bturkish\b',
 'indian':r'индийск|үнді|\bindian\b',
 'french':r'француз|\bfrench\b',
 'uzbek':r'узбек|өзбек|\buzbek\b',
 'russian':r'русск\w*\s+кухн|орыс\w*\s+ас|\brussian\s+food\b',
 'thai':r'тайск|тай\s+ас|\bthai\b',
 'mexican':r'мексикан|\bmexican\b',
}
DIETS={'halal':r'халяль|халал|адал\s+ас|\bhalal\b',
 'vegan':r'веган|\bvegan\b',
 'vegetarian':r'вегетариан|\bvegetarian\b',
 'gluten_free':r'без\s+глютен|глютенсіз|gluten.free'}

def clean_requirements(values):
    if not isinstance(values,list) or len(values)>12: raise ValueError('Invalid food requirements')
    result=[]
    for item in values:
        if not isinstance(item,dict) or item.get('type') not in ('dish','cuisine','diet'): raise ValueError('Invalid food constraint')
        value=item.get('value')
        if not isinstance(value,str) or not re.fullmatch(r'[\w -]{1,60}',value,re.UNICODE): raise ValueError('Invalid food value')
        req={'type':item['type'],'value':value.strip().lower().replace(' ','_')}
        if req not in result: result.append(req)
    return result

def food_request(query):
    q=query.lower().replace('ё','е')
    requirements=[]
    for kind,patterns in [('dish',ALIASES),('cuisine',CUISINES),('diet',DIETS)]:
        for value,pattern in patterns.items():
            if re.search(pattern,q):requirements.append({'type':kind,'value':value})
    # Ingredient exclusions/allergies cannot be established from a generic cuisine tag.
    unknown=bool(re.search(r'аллерг|аллергия|allerg|без\s+(?:орех|арахис|молок|лактоз|мяс)|жаңғақсыз|сүтсіз|nut.free|lactose.free|dairy.free',q))
    return requirements,unknown

def evidence_for(place,requirements,unknown=False):
    """All explicit requirements need matching source tags. No name/description inference."""
    if unknown:return None
    tags=place.get('food_tags') or {}
    raw=tags.get('cuisine','')
    cuisines={v.strip().lower() for v in raw.split(';') if v.strip()}
    evidence=[]
    for req in requirements:
        if req['type'] in ('dish','cuisine'):
            if req['value'] not in cuisines:
                proof=cuisine_evidence(place,req)
                if proof is None:return None
            else:proof={'tag':'cuisine','value':raw,'provider':'OpenStreetMap','source':place.get('source')}
        else:
            tag='diet:'+req['value']
            if tags.get(tag,'').lower() not in ('yes','only'):return None
            proof={'tag':tag,'value':tags[tag]}
        if proof not in evidence:evidence.append(proof)
    return evidence

def needs_specific_food_check(query):
    """Fail closed for unrecognised food words when a semantic parse is unavailable."""
    q=query.lower().replace('ё','е')
    if not re.search(r'поесть|покуш|съесть|заказа|\beat\b|food|hungry|тамақ|жегім',q):return False
    # Ignore practical constraints after punctuation; recognise specificity in each food clause.
    generic=set('трое троих троем троём четверо четверых четвером пятеро пятерых пятером человека человек участника участников группа группы группой компания компанией people persons group of three four five бірге адам үшеуміз төртеуміз бесеуміз сытно очень сильно голоден уютное уютный уютно недорогой бюджетный недорогая место заведение somewhere anything something tasty delicious affordable cheap something really я мы мне нам ты хочу хотим хочется можно где бы как что нибудь просто вкусно вкусный вкусное поесть покушать съесть перекусить обед ужин завтрак пообедать поужинать позавтракать голодная голодный голодные рядом недалеко поблизости ресторан кафе хороший хорошее место для еды и или с без ребенком детьми семьей нас один вдвоем компанией сейчас сегодня быстро недорого не больше меньше дальше минут мин пешком идти идтись час часа часов до есть у меня только в на а от возле байтерек байтерека экспо минутами i we am are want would like to eat food hungry somewhere near nearby me us a an the good nice place restaurant cafe quick quickly lunch dinner breakfast with my child kids family and or no more than minutes min walk walking hour hours within away at for please хочу тамақ жегім келеді ішкім жақын маған мен баламмен жерде'.split())
    for clause in re.split(r'[,;.!?]',q):
        if not re.search(r'поесть|покуш|съесть|заказа|\beat\b|food|hungry|тамақ|жегім',clause):continue
        words=re.findall(r'[^\W\d_]+',clause)
        if any(word not in generic for word in words):return True
    return False
