import os,uuid,json,threading,io
from datetime import date
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI,HTTPException,Request,UploadFile,File
from fastapi.responses import FileResponse,Response,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel,Field
from db import init,query,required,connect
from ai import ready,config_check,save_media,generate,recover
ROOT=Path(__file__).parent

@asynccontextmanager
async def lifespan(app):
    if os.getenv('DATABASE_URL'):
        init()
        threading.Thread(target=recover,daemon=True).start()
    yield

app=FastAPI(title='Godnatt',lifespan=lifespan,docs_url=None,redoc_url=None)

@app.middleware('http')
async def security(request:Request,call_next):
    if request.method not in ('GET','HEAD','OPTIONS'):
        origin=request.headers.get('origin')
        if origin and origin.rstrip('/')!=str(request.base_url).rstrip('/') and origin!=os.getenv('PUBLIC_ORIGIN'):
            return JSONResponse({'detail':'Begäran måste komma från Godnatt.'},403)
        if int(request.headers.get('content-length','0'))>13*1024*1024:
            return JSONResponse({'detail':'Filen är för stor.'},413)
    r=await call_next(request)
    r.headers['X-Content-Type-Options']='nosniff'
    r.headers['Referrer-Policy']='same-origin'
    r.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' blob: data:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
    if request.url.path.startswith('/api/'):r.headers['Cache-Control']='no-store'
    return r

@app.exception_handler(Exception)
async def error(request,exc):
    return JSONResponse({'detail':'Tjänsten kunde inte slutföra begäran. Dina sparade uppgifter finns kvar. Försök igen.'},503)

def newid():return str(uuid.uuid4())
class Family(BaseModel):name:str=Field(min_length=1,max_length=100)
class Person(BaseModel):
    name:str=Field(min_length=1,max_length=100)
    age:float=Field(ge=0,le=120)
    gender:str=Field(default='',max_length=50)
class Relation(BaseModel):
    source_id:str
    target_id:str
    role:str=Field(min_length=1,max_length=80)
class Memory(BaseModel):
    text:str=Field(min_length=1,max_length=5000)
    event_date:date
class Order(BaseModel):
    person_id:str
    page_count:int=Field(ge=1,le=20)
    prompt:str=Field(default='',max_length=5000)
    request_key:str=Field(min_length=16,max_length=100)

@app.get('/api/status')
def status():
    return {'database':bool(os.getenv('DATABASE_URL')),'ai':ready(),'open_access':True}

@app.get('/healthz')
def health():
    query('SELECT 1')
    return {'ok':True}

@app.get('/api/families')
def families():return query('SELECT * FROM families ORDER BY created_at')

@app.post('/api/families',status_code=201)
def create_family(f:Family):
    id=newid();query('INSERT INTO families(id,name) VALUES(%s,%s)',(id,f.name.strip()));return required('families',id)

@app.get('/api/families/{id}')
def family(id:str):
    f=required('families',id)
    f['people']=query('SELECT * FROM people WHERE family_id=%s ORDER BY created_at',(id,))
    f['relations']=query('SELECT r.* FROM relations r JOIN people p ON p.id=r.source_id WHERE p.family_id=%s',(id,))
    f['memories']=query('SELECT m.* FROM memories m JOIN people p ON p.id=m.person_id WHERE p.family_id=%s ORDER BY m.event_date DESC,m.created_at DESC',(id,))
    f['books']=query('SELECT b.id,b.title,b.status,b.error,b.page_count,b.prompt,b.created_at,(SELECT image_id FROM pages WHERE book_id=b.id ORDER BY number LIMIT 1) AS cover,(SELECT count(*) FROM pages WHERE book_id=b.id) AS progress FROM books b WHERE family_id=%s ORDER BY created_at DESC',(id,))
    return f

@app.post('/api/families/{id}/people',status_code=201)
def add_person(id:str,p:Person):
    required('families',id);pid=newid()
    query('INSERT INTO people(id,family_id,name,age,gender) VALUES(%s,%s,%s,%s,%s)',(pid,id,p.name.strip(),p.age,p.gender));return required('people',pid)

@app.put('/api/people/{id}')
def edit_person(id:str,p:Person):
    required('people',id);query('UPDATE people SET name=%s,age=%s,gender=%s WHERE id=%s',(p.name.strip(),p.age,p.gender,id));return required('people',id)

@app.delete('/api/people/{id}')
def delete_person(id:str):
    required('people',id)
    if query("SELECT id FROM books WHERE person_id=%s AND status IN ('queued','generating')",(id,)):
        raise HTTPException(409,'Vänta tills boken har skapats innan du tar bort personen.')
    query('DELETE FROM people WHERE id=%s',(id,));return {'ok':True}

@app.post('/api/families/{id}/relations',status_code=201)
def add_relation(id:str,r:Relation):
    a=required('people',r.source_id);b=required('people',r.target_id)
    if a['family_id']!=id or b['family_id']!=id or r.source_id==r.target_id:raise HTTPException(422,'Välj två olika personer i samma familj.')
    rid=newid()
    return query('INSERT INTO relations(id,source_id,target_id,role) VALUES(%s,%s,%s,%s) ON CONFLICT(source_id,target_id,role) DO UPDATE SET role=excluded.role RETURNING *',(rid,r.source_id,r.target_id,r.role.strip()),True)

@app.delete('/api/relations/{id}')
def delete_relation(id:str):
    query('DELETE FROM relations WHERE id=%s',(id,));return {'ok':True}

@app.post('/api/people/{id}/photo')
def upload_photo(id:str,file:UploadFile=File()):
    required('people',id)
    data=file.file.read(12*1024*1024+1)
    try:mid=save_media(data)
    except (ValueError,OSError):raise HTTPException(422,'Välj en giltig JPG-, PNG- eller WebP-bild under 12 MB.')
    query('UPDATE people SET photo_id=%s WHERE id=%s',(mid,id))
    return {'photo_id':mid}

@app.delete('/api/people/{id}/photo')
def delete_photo(id:str):
    required('people',id);query('UPDATE people SET photo_id=NULL WHERE id=%s',(id,));return {'ok':True}

@app.get('/api/media/{id}')
def media(id:str):
    m=required('media',id);return Response(bytes(m['data']),media_type=m['mime'])

@app.post('/api/people/{id}/memories',status_code=201)
def add_memory(id:str,m:Memory):
    required('people',id);mid=newid()
    query('INSERT INTO memories(id,person_id,text,original_text,original_event_date,event_date) VALUES(%s,%s,%s,%s,%s,%s)',(mid,id,m.text,m.text,m.event_date,m.event_date))
    return required('memories',mid)

@app.put('/api/memories/{id}')
def edit_memory(id:str,m:Memory):
    required('memories',id);query('UPDATE memories SET text=%s,event_date=%s,updated_at=now() WHERE id=%s',(m.text,m.event_date,id))
    return required('memories',id)

@app.delete('/api/memories/{id}')
def delete_memory(id:str):
    query('DELETE FROM memories WHERE id=%s',(id,));return {'ok':True}

@app.get('/api/budget')
def budget():return query('SELECT limit_ore,committed_ore,storage_bytes FROM budget WHERE id=1',one=True)

@app.post('/api/families/{id}/books',status_code=202)
def create_book(id:str,o:Order):
    old=query('SELECT id,family_id FROM books WHERE request_key=%s',(o.request_key,),True)
    if old:
        if old['family_id']!=id:raise HTTPException(409,'Beställningen finns redan.')
        return {'id':old['id']}
    config_check()
    f=family(id);child=next((p for p in f['people'] if p['id']==o.person_id),None)
    if not child:raise HTTPException(422,'Välj en person i familjen.')
    if sum(bool(p['photo_id']) for p in f['people'])>8:raise HTTPException(422,'Boken kan använda högst åtta personfoton.')
    snapshot={'child':child,'people':f['people'],'relations':f['relations'],'memories':f['memories'],'created_at':date.today().isoformat()}
    snap=json.dumps(jsonable_encoder(snapshot),ensure_ascii=False)
    if len(snap.encode())>50000:raise HTTPException(422,'Underlaget är för stort för en bok. Inga minnen har tagits bort.')
    idb=newid()
    with connect() as c:
        # Serialize admission with budget calls. Every request still reserves atomically before its API call.
        b=c.execute('SELECT * FROM budget WHERE id=1 FOR UPDATE').fetchone()
        if b['committed_ore']+int(os.environ['IMAGE_CALL_MAX_ORE'])*o.page_count+100>b['limit_ore']:
            raise HTTPException(402,'AI-budgeten räcker inte till denna bok.')
        inserted=c.execute('INSERT INTO books(id,family_id,person_id,page_count,prompt,snapshot,request_key) VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s) ON CONFLICT(request_key) DO NOTHING RETURNING id',(idb,id,o.person_id,o.page_count,o.prompt,snap,o.request_key)).fetchone()
        if not inserted:return {'id':c.execute('SELECT id FROM books WHERE request_key=%s',(o.request_key,)).fetchone()['id']}
    threading.Thread(target=generate,args=(idb,),daemon=True).start()
    return {'id':idb}

@app.get('/api/books/{id}')
def book(id:str):
    b=required('books',id)
    b['progress']=query('SELECT count(*) AS n FROM pages WHERE book_id=%s',(id,),True)['n']
    b['pages']=query('SELECT number,text,image_id FROM pages WHERE book_id=%s ORDER BY number',(id,)) if b['status']=='ready' else []
    b.pop('story',None)
    return b

@app.get('/')
@app.get('/book/{book_id}')
def index(book_id:str=''):return FileResponse(ROOT/'static/index.html')

@app.get('/sw.js')
def sw():return FileResponse(ROOT/'static/sw.js',media_type='application/javascript',headers={'Cache-Control':'no-cache','Service-Worker-Allowed':'/'})

app.mount('/',StaticFiles(directory=ROOT/'static'),name='static')
