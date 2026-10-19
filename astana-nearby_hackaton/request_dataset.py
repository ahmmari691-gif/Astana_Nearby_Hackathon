# -*- coding: utf-8 -*-
"""Save reproducible provider batches after intent extraction, without keys or raw user text."""
import datetime,hashlib,json,pathlib,os,tempfile
ROOT=pathlib.Path(__file__).resolve().parent

def save_batch(profile,places):
    filters={k:profile.get(k) for k in ('include','exclude','food_requirements')}
    identity=json.dumps(filters,ensure_ascii=False,sort_keys=True)
    directory=ROOT/'data/request-datasets';directory.mkdir(parents=True,exist_ok=True)
    target=directory/(hashlib.sha256(identity.encode()).hexdigest()[:24]+'.json')
    payload={'source':'2ГИС','collected_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'method':'Gemini/local intent extraction followed by official 2GIS Places API search',
             'filters':filters,'count':len(places),'complete_city':False,'places':places}
    fd,name=tempfile.mkstemp(prefix='batch-',suffix='.tmp',dir=directory)
    try:
        with os.fdopen(fd,'w',encoding='utf8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
        os.replace(name,target)
    finally:
        if os.path.exists(name):os.unlink(name)
    # Bound accumulated snapshots; never retain raw prompts or API keys.
    files=sorted(directory.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)
    for path in files[100:]:path.unlink(missing_ok=True)
