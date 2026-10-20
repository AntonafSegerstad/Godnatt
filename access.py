import hashlib,hmac,secrets
from datetime import datetime,timezone,timedelta
from fastapi import HTTPException
from db import connect,query

def digest(value):return hashlib.sha256(value.encode()).hexdigest()
def pin_hash(pin):
    salt=secrets.token_hex(16)
    return salt+':'+hashlib.scrypt(pin.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()
def matches(pin,stored):
    if not stored:return False
    salt,expected=stored.split(':')
    return hmac.compare_digest(expected,hashlib.scrypt(pin.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex())
def grant(c,fid,response):
    token=secrets.token_urlsafe(32)
    c.execute('DELETE FROM family_sessions WHERE expires_at<now()')
    c.execute("INSERT INTO family_sessions(token_hash,family_id,expires_at) VALUES(%s,%s,now()+interval '12 hours')",(digest(token),fid))
    response.set_cookie('gn_'+fid,token,max_age=43200,httponly=True,secure=True,samesite='strict',path='/')
def unlock(fid,pin,response):
    failure=None
    with connect() as c:
        f=c.execute('SELECT * FROM families WHERE id=%s FOR UPDATE',(fid,)).fetchone()
        if not f:raise HTTPException(404,'Familjen finns inte längre.')
        if not f['pin_hash']:raise HTTPException(403,'Familjen behöver först välja PIN via sin inställningslänk.')
        if f['pin_locked_until'] and f['pin_locked_until']>datetime.now(timezone.utc):
            failure=HTTPException(429,'För många försök. Vänta fem minuter och försök igen.')
        elif matches(pin,f['pin_hash']):
            c.execute('UPDATE families SET pin_failures=0,pin_locked_until=NULL WHERE id=%s',(fid,));grant(c,fid,response)
        else:
            failures=(0 if f['pin_locked_until'] else f['pin_failures'])+1
            c.execute('UPDATE families SET pin_failures=%s,pin_locked_until=%s WHERE id=%s',(failures,datetime.now(timezone.utc)+timedelta(minutes=5) if failures>=5 else None,fid))
            failure=HTTPException(401,'Fel PIN-kod.')
    if failure:raise failure
    return {'ok':True}
def setup(fid,token,pin,response):
    with connect() as c:
        f=c.execute('SELECT * FROM families WHERE id=%s FOR UPDATE',(fid,)).fetchone()
        if not f or f['pin_hash'] or not f['pin_setup_hash'] or not hmac.compare_digest(digest(token),f['pin_setup_hash']):
            raise HTTPException(403,'Länken är ogiltig eller har redan använts.')
        c.execute('UPDATE families SET pin_hash=%s,pin_setup_hash=NULL WHERE id=%s',(pin_hash(pin),fid));grant(c,fid,response)
    return {'ok':True}
def authorization(request):
    parts=request.url.path.strip('/').split('/')
    if len(parts)<3 or parts[0]!='api':return
    resource,id=parts[1:3]
    if resource=='families' and len(parts)==4 and parts[3] in ('unlock','pin-setup'):return
    candidates=[]
    if resource=='families':candidates=query('SELECT id AS family_id FROM families WHERE id=%s',(id,))
    elif resource in ('people','books'):
        candidates=query(f'SELECT family_id FROM {resource} WHERE id=%s',(id,))
    elif resource=='memories':candidates=query('SELECT p.family_id FROM memories m JOIN people p ON p.id=m.person_id WHERE m.id=%s',(id,))
    elif resource=='relations':candidates=query('SELECT p.family_id FROM relations r JOIN people p ON p.id=r.source_id WHERE r.id=%s',(id,))
    elif resource=='media':
        candidates=query('SELECT family_id FROM people WHERE photo_id=%s UNION SELECT b.family_id FROM pages p JOIN books b ON b.id=p.book_id WHERE p.image_id=%s UNION SELECT family_id FROM books WHERE snapshot::text LIKE %s',(id,id,'%'+id+'%'))
    else:return
    if not candidates:raise HTTPException(404,'Det finns inte längre.')
    for row in candidates:
        fid=row['family_id'];token=request.cookies.get('gn_'+fid,'')
        if token and query('SELECT 1 FROM family_sessions WHERE family_id=%s AND token_hash=%s AND expires_at>now()',(fid,digest(token)),True):return
    raise HTTPException(401,{'message':'Ange familjens PIN-kod.','family_id':candidates[0]['family_id']})
