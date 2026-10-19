# -*- coding: utf-8 -*-
"""Conservative rules for time-sensitive requests; source facts remain separate from wishes."""
import datetime,re

def airport_request(query):
    return bool(re.search(r'перед\s+вылет|до\s+вылет|before\s+(?:my\s+)?flight|ұшу\s+алдында',query,re.I))

def night_request(query):
    return bool(re.search(r'ноч|\bnight\b|түн',query,re.I))

def interactive_requested(query):
    return bool(re.search(r'интерактив|interactive|интерактивті',query,re.I))

def open_for_visit(place,walk,visit,now=None):
    """Schedule evidence for arrival and the entire visit, in Astana UTC+5."""
    now=now or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5)))
    schedule=place.get('schedule')
    if not isinstance(schedule,dict):return False
    start=now+datetime.timedelta(minutes=walk);end=start+datetime.timedelta(minutes=visit)
    days=('Mon','Tue','Wed','Thu','Fri','Sat','Sun')
    for offset in (-1,0):
        date=start.date()+datetime.timedelta(days=offset)
        for interval in (schedule.get(days[date.weekday()]) or {}).get('working_hours',[]):
            try:
                def at(text):
                    hour,minute=map(int,text.split(':'));return datetime.datetime.combine(date,datetime.time(tzinfo=start.tzinfo))+datetime.timedelta(hours=hour,minutes=minute)
                opening=at(interval['from']);closing=at(interval['to'])
                if closing<=opening:closing+=datetime.timedelta(days=1)
                if opening<=start and end<=closing:return True
            except (ValueError,TypeError,KeyError,AttributeError):continue
    return False


def schedule_for_day(place,reference):
    """Weekly schedule for the request's Astana date, not evidence of current opening."""
    zone=datetime.timezone(datetime.timedelta(hours=5))
    date=reference.astimezone(zone)
    result={'date':date.date().isoformat(),'status':'unknown','intervals':[]}
    schedule=place.get('schedule')
    if isinstance(schedule,dict):
        day=schedule.get(('Mon','Tue','Wed','Thu','Fri','Sat','Sun')[date.weekday()])
        if isinstance(day,dict):
            if day.get('is_closed') is True:result['status']='day_off';return result
            for interval in day.get('working_hours') or []:
                start=interval.get('from');end=interval.get('to')
                if isinstance(start,str) and isinstance(end,str) and re.fullmatch(r'(?:[01]\d|2[0-4]):[0-5]\d',start) and re.fullmatch(r'(?:[01]\d|2[0-4]):[0-5]\d',end):
                    result['intervals'].append({'from':start,'to':end})
            if result['intervals']:result['status']='listed'
    elif place.get('hours')=='24/7':result.update(status='listed',intervals=[{'from':'00:00','to':'24:00'}])
    return result
