# -*- coding: utf-8 -*-
"""Indexed on-disk city catalogue. Only nearby rows are decoded per request."""
import json,math,os,pathlib,sqlite3,tempfile
from contextlib import closing
ROOT=pathlib.Path(__file__).resolve().parent
DB=ROOT/'data/catalog.sqlite'

def build(places,metadata,path=DB):
    path=pathlib.Path(path);path.parent.mkdir(exist_ok=True,parents=True)
    fd,temp=tempfile.mkstemp(prefix='catalog-',suffix='.next',dir=path.parent);os.close(fd)
    connection=None
    try:
        connection=sqlite3.connect(temp)
        connection.executescript('''
          CREATE TABLE places (id INTEGER PRIMARY KEY, osm_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL, kind TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL, data TEXT NOT NULL);
          CREATE INDEX places_kind ON places(kind);
          CREATE INDEX places_name ON places(name COLLATE NOCASE);
          CREATE VIRTUAL TABLE spatial USING rtree(id,min_lat,max_lat,min_lon,max_lon);
          CREATE TABLE metadata (key TEXT PRIMARY KEY,value TEXT NOT NULL);
        ''')
        seen=set();count=0
        for place in places:
            if place['id'] in seen:continue
            seen.add(place['id']);count+=1
            cur=connection.execute('INSERT INTO places(osm_id,name,kind,lat,lon,data) VALUES(?,?,?,?,?,?)',
                (place['id'],place['name'],place['kind'],place['lat'],place['lon'],json.dumps(place,ensure_ascii=False)))
            connection.execute('INSERT INTO spatial VALUES(?,?,?,?,?)',(cur.lastrowid,place['lat'],place['lat'],place['lon'],place['lon']))
        metadata=dict(metadata,count=count)
        connection.executemany('INSERT INTO metadata VALUES(?,?)',[(k,json.dumps(v,ensure_ascii=False)) for k,v in metadata.items()])
        connection.commit()
        if connection.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Database integrity check failed')
        connection.execute('ANALYZE');connection.commit();connection.close();connection=None
        os.replace(temp,path)
        return metadata
    finally:
        if connection is not None:connection.close()
        if os.path.exists(temp):os.unlink(temp)

def connect(path=DB):
    return sqlite3.connect(pathlib.Path(path).resolve().as_uri()+'?mode=ro',uri=True,timeout=3)

def summary(path=DB):
    with closing(connect(path)) as c:return {k:json.loads(v) for k,v in c.execute('SELECT key,value FROM metadata')}

def nearby(lat,lon,radius,kinds=None,path=DB,query=''):
    lat_delta=radius/110500.0;lon_delta=radius/(110500.0*max(0.1,math.cos(math.radians(lat))))
    clauses=['r.max_lat>=?','r.min_lat<=?','r.max_lon>=?','r.min_lon<=?']
    values=[lat-lat_delta,lat+lat_delta,lon-lon_delta,lon+lon_delta]
    if kinds is not None:
        if not kinds:return []
        clauses.append('p.kind IN ('+','.join('?' for _ in kinds)+')');values.extend(sorted(kinds))
    # Name matching happens on the bounded spatial candidates, never in the browser.
    sql='SELECT p.data FROM spatial r JOIN places p ON p.id=r.id WHERE '+' AND '.join(clauses)
    with closing(connect(path)) as c:rows=c.execute(sql,values).fetchall()
    result=[json.loads(row[0]) for row in rows]
    if query:
        q=query.casefold();result=[p for p in result if q in (p['name']+' '+p.get('category','')).casefold()]
    return result
