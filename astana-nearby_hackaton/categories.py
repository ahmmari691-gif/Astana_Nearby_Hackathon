# -*- coding: utf-8 -*-
"""Shared extra leisure categories: matching, provider queries and UI labels."""
PARK_PATTERN=r'\b(?:парк(?:и|а|е|у|ом|ов|ам|ами|ах)?|сквер(?:ы|а|е|у|ом|ов|ам|ами|ах)?|parks?|саябақ\w*)\b'
GARDEN_PATTERN=r'\b(?:сад(?:ы|а|у|е|ом|ов|ам|ами|ах)?|gardens?|ботаническ\w*\s+сад\w*|бақ)\b'
KINDERGARTEN_PATTERN=r'детск\w*\s+сад\w*|ясли|дошкольн|\bkindergartens?\b|\bpreschools?\b|\bnurser(?:y|ies)\b|балабақша\w*|бала\s*бақша\w*'

def kindergarten_category(text):
 import re
 return bool(re.search(KINDERGARTEN_PATTERN,text,re.I))

PARKING_PATTERN=r'парков|автостоян|автопарк|паркинг|\bparking\b|\bcar\s+parks?\b|тұрақ'

def parking_category(text):
 import re
 return bool(re.search(PARKING_PATTERN,text,re.I)) and not bool(re.search(PARK_PATTERN,re.sub(r'\bcar\s+parks?\b','',text,flags=re.I),re.I))

WALKING={
 'promenade':('набережные',r'набереж|embankment|waterfront|жағалау',('Набережная','Жағалау','Waterfront'),25),
 'boulevard':('бульвары',r'бульвар|boulevard',('Бульвар','Бульвар','Boulevard'),25),
 'square':('площади',r'\bплощад(?:ь|и|ей)\b|\bsquares?\b|алаңдар',('Площадь','Алаң','Square'),20),
 'pedestrian':('пешеходные улицы',r'пешеходн|pedestrian|жаяу.*көше',('Пешеходная улица','Жаяу көше','Pedestrian street'),25),
 'street':('улицы',r'\bулиц(?:а|ы|е|у|ей|ам|ами|ах)\b|\bstreets?\b|көше',('Городская улица','Қала көшесі','City street'),25),
 'architecture':('памятники архитектуры',r'архитектур|architecture|сәулет|интересн\w*\s+здани|историческ\w*\s+здани|объект\w*\s+культурн\w*\s+наслед|historic\w*\s+building',('Архитектурное место','Сәулет нысаны','Architectural landmark'),20),
}
EXTRA={
 'theatre':('театры',r'театр|theat(?:re|er)',('Театр','Театр','Theatre'),90),
 'concert':('концертные залы',r'концерт|живая\s+музык|concert|live music',('Концертная площадка','Концерт алаңы','Concert venue'),90),
 'bar':('бары',r'\bбар(?:ы|е|ов)?\b|\bbars?\b',('Бар','Бар','Bar'),45),
 'pub':('пабы',r'\bпаб\w*|\bpubs?\b',('Паб','Паб','Pub'),45),
 'quest':('квесты',r'квест|escape room|quest',('Квест','Квест','Escape room'),60),
 'vr':('клубы виртуальной реальности',r'виртуальн|\bvr\b',('VR-клуб','VR клуб','VR venue'),45),
 'gaming':('компьютерные клубы',r'компьютерн\w*\s+клуб|игров\w*\s+клуб|gaming|esports',('Игровой клуб','Ойын клубы','Gaming venue'),60),
 'trampoline':('батутные центры',r'батут|trampoline',('Батутный центр','Батут орталығы','Trampoline centre'),45),
 'amusement':('аттракционы',r'аттракцион|amusement',('Аттракционы','Аттракциондар','Amusement rides'),45),
 'kids_centre':('детские развлекательные центры',r'детск\w*\s+(?:развлекательн\w*\s+)?центр|kids.*cent(?:re|er)|балалар.*ортал',('Детский центр','Балалар орталығы','Children’s activity centre'),60),
 'pool':('бассейны',r'бассейн|swimming|\bpool\b',('Бассейн','Бассейн','Swimming pool'),60),
 'waterpark':('аквапарки',r'аквапарк|waterpark|water park',('Аквапарк','Аквапарк','Water park'),90),
 'rink':('катки',r'каток|катки|коньк|ice rink|skating|мұз айдын',('Каток','Мұз айдыны','Ice rink'),45),
 'sports':('спортивные площадки',r'спортивн\w*\s+площад|спортзал|sports? ground|\bgym\b',('Спортивная площадка','Спорт алаңы','Sports venue'),45),
 'spa':('спа',r'\bспа\b|\bspa\b',('СПА','СПА','Spa'),60),
 'sauna':('бани и сауны',r'\bбан[яиюь]\w*|саун|sauna|bathhouse|монша',('Баня / сауна','Монша / сауна','Bathhouse / sauna'),60),
 'mall':('торговые центры',r'торгов[\w-]*\s+(?:центр|комплекс)|\bтрц\b|\bmall\b|shopping cent',('Торговый центр','Сауда орталығы','Shopping centre'),45),
 'shop':('магазины',r'магазин|шопинг|shopping|\bshops?\b|дүкен',('Магазин','Дүкен','Shop'),30),
 'tour':('экскурсии',r'экскурс|\bгид\w*|guided tour|tour guide|экскурсия',('Экскурсионная служба','Экскурсия қызметі','Tour provider'),60),
}

EXTRA.update(WALKING)

def provider_kind(label):
 import re
 # Specific forms precede general ones, e.g. water parks before parks.
 if re.search(r'бюро|проектир|design office',label,re.I) and re.search(r'архитектур|architecture',label,re.I):return None
 return next((key for key,value in EXTRA.items() if re.search(value[1],label,re.I)),None)


def walking_categories(label):
 import re
 if kindergarten_category(label) or parking_category(label):return []
 if re.search(r'бюро|проектир|design office|архитектурн\w*\s+(?:студи|компан|мастерск)',label,re.I):return []
 result=[key for key,value in WALKING.items() if key!='street' and re.search(value[1],label,re.I)]
 if re.search(r'достопримеч|памятник|скульптур|памятн\w*\s+доск|фонтан|\bmonuments?\b|sculptur|fountains?|ескерткіш',label,re.I):result.append('attraction')
 return result
