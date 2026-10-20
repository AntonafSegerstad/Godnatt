import os
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from fastapi import HTTPException

def connect():
    url=os.getenv('DATABASE_URL')
    if not url: raise HTTPException(503,'Databasen är inte ansluten ännu.')
    from urllib.parse import urlparse
    if '-pooler.' in (urlparse(url).hostname or ''):raise HTTPException(503,'Servern behöver databasens direkta anslutning för säkra bokjobb.')
    return psycopg.connect(url,row_factory=dict_row,connect_timeout=10)

def init():
    with connect() as c: c.execute(Path(__file__).with_name('schema.sql').read_text())

def query(sql,args=(),one=False):
    with connect() as c:
        cur=c.execute(sql,args)
        if not cur.description:return None
        return cur.fetchone() if one else cur.fetchall()

def required(table,id):
    assert table in ('families','people','memories','books','media','relations')
    row=query(f'SELECT * FROM {table} WHERE id=%s',(id,),True)
    if not row:raise HTTPException(404,'Det finns inte längre.')
    return row
