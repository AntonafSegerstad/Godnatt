import os,io,json,uuid
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException
from PIL import Image

def dummy_book(f,p):
    from db import query
    id=str(uuid.uuid4())
    query("INSERT INTO books(id,family_id,person_id,page_count,prompt,snapshot,request_key) VALUES(%s,%s,%s,2,'test',%s::jsonb,%s)",(id,f['id'],p['id'],json.dumps({'child':p,'people':[p],'relations':[],'memories':[]},default=str),str(uuid.uuid4())))
    return id

def test_family_and_person_edit(client,family):
    f,p=family
    assert float(p['age'])==1.5
    r=client.put('/api/people/'+p['id'],json={'name':'Rättat testnamn','age':2,'gender':'pojke'})
    assert r.status_code==200 and r.json()['name']=='Rättat testnamn'
    assert client.get('/api/families/'+f['id']).json()['people'][0]['name']=='Rättat testnamn'

def test_multiple_targeted_relations_and_isolation(client,family):
    f,p=family
    other=client.post('/api/families/'+f['id']+'/people',json={'name':'Testförälder','age':35}).json()
    for role in ['pappa','tränare']:
        assert client.post('/api/families/'+f['id']+'/relations',json={'source_id':other['id'],'target_id':p['id'],'role':role}).status_code==201
    rs=client.get('/api/families/'+f['id']).json()['relations']
    assert len(rs)==2 and all(r['target_id']==p['id'] for r in rs)
    assert client.post('/api/families/'+f['id']+'/relations',json={'source_id':p['id'],'target_id':p['id'],'role':'kompis'}).status_code==422
    foreign=client.post('/api/families',json={'name':'ANNAN TESTFAMILJ'}).json()
    assert client.post('/api/families/'+foreign['id']+'/relations',json={'source_id':other['id'],'target_id':p['id'],'role':'kompis'}).status_code==422
    assert client.delete('/api/relations/'+rs[0]['id']).status_code==200

def test_memories_preserve_original_and_dates(client,family):
    f,p=family
    m=client.post('/api/people/'+p['id']+'/memories',json={'text':'Spelade fotboll','event_date':'2026-10-20'}).json()
    n=client.put('/api/memories/'+m['id'],json={'text':'Spelade innebandy','event_date':'2026-10-19'}).json()
    assert n['original_text']=='Spelade fotboll'
    assert n['original_event_date']=='2026-10-20'
    assert n['event_date']=='2026-10-19' and n['created_at']==m['created_at']
    assert client.delete('/api/memories/'+m['id']).status_code==200
    assert not client.get('/api/families/'+f['id']).json()['memories']

def test_photo_stored_as_valid_image(client,family):
    f,p=family
    buf=io.BytesIO();Image.new('RGB',(100,100),'red').save(buf,'PNG')
    r=client.post('/api/people/'+p['id']+'/photo',files={'file':('test.png',buf.getvalue(),'image/png')})
    assert r.status_code==200
    photo=client.get('/api/media/'+r.json()['photo_id'])
    assert photo.status_code==200 and photo.headers['content-type']=='image/jpeg'
    assert client.post('/api/people/'+p['id']+'/photo',files={'file':('bad.svg',b'<svg><script>bad</script></svg>','image/svg+xml')}).status_code==422
    assert client.delete('/api/people/'+p['id']+'/photo').status_code==200

def test_ai_fails_closed_without_config(client,family,monkeypatch):
    f,p=family
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    r=client.post('/api/families/'+f['id']+'/books',json={'person_id':p['id'],'page_count':5,'request_key':str(uuid.uuid4())})
    assert r.status_code==503
    assert not client.get('/api/families/'+f['id']).json()['books']

def test_input_limits_and_cross_origin(client,family):
    f,p=family
    assert client.post('/api/families/'+f['id']+'/books',json={'person_id':p['id'],'page_count':0,'request_key':str(uuid.uuid4())}).status_code==422
    assert client.post('/api/families',json={'name':'bad'},headers={'origin':'https://other.example'}).status_code==403
    assert client.post('/api/families',json={'name':'good'},headers={'origin':'http://testserver'}).status_code==201

def test_atomic_budget_under_concurrency(client,family):
    from db import query
    from ledger import reserve,settle
    f,p=family;b=dummy_book(f,p)
    query('UPDATE budget SET committed_ore=0,limit_ore=50000 WHERE id=1')
    def attempt(i):
        try:return reserve(b,'parallel:'+str(i),10000)
        except HTTPException as e:assert e.status_code==402;return None
    with ThreadPoolExecutor(max_workers=12) as pool:ids=list(pool.map(attempt,range(12)))
    assert len([i for i in ids if i])==5
    assert query('SELECT committed_ore FROM budget WHERE id=1',one=True)['committed_ore']==50000
    first=next(i for i in ids if i);settle(first,None)
    assert query('SELECT committed_ore FROM budget WHERE id=1',one=True)['committed_ore']==50000
    settle(first,4000);settle(first,4000)
    assert query('SELECT committed_ore FROM budget WHERE id=1',one=True)['committed_ore']==44000
    query('UPDATE budget SET committed_ore=0,limit_ore=50000 WHERE id=1')

def test_duplicate_charge_and_unknown_usage(client,family):
    from db import query
    from ledger import reserve,settle
    f,p=family;b=dummy_book(f,p)
    cid=reserve(b,'text',100)
    try:reserve(b,'text',100);assert False
    except HTTPException as e:assert e.status_code==409
    settle(cid,None)
    assert query('SELECT state FROM charges WHERE id=%s',(cid,),True)['state']=='reserved'

def test_interruption_keeps_reservation(client,family):
    from db import query
    from ledger import reserve
    from ai import recover
    f,p=family;b=dummy_book(f,p)
    query("UPDATE books SET status='generating' WHERE id=%s",(b,))
    cid=reserve(b,'image:1',100)
    # Other artificial queue rows must not be sent to an API.
    query("UPDATE books SET status='failed' WHERE status='queued'")
    recover()
    assert client.get('/api/books/'+b).json()['status']=='failed'
    assert query('SELECT state FROM charges WHERE id=%s',(cid,),True)['state']=='reserved'

def test_book_cross_client_and_restart(client,family):
    from db import query,init
    from ai import save_media
    from fastapi.testclient import TestClient
    from app import app
    f,p=family;b=dummy_book(f,p)
    buf=io.BytesIO();Image.new('RGB',(10,10)).save(buf,'PNG');mid=save_media(buf.getvalue())
    for n in [1,2]:query('INSERT INTO pages(book_id,number,text,image_id) VALUES(%s,%s,%s,%s)',(b,n,'FIKTIV TESTSIDA',mid))
    query("UPDATE books SET status='ready',title='FIKTIV TESTBOK' WHERE id=%s",(b,))
    init()
    second=TestClient(app)
    loaded=second.get('/api/books/'+b).json()
    assert loaded['status']=='ready' and len(loaded['pages'])==2
    assert second.get('/book/'+b).status_code==200
    assert second.get('/api/media/'+mid).status_code==200
    client.delete('/api/people/'+p['id'])
    assert second.get('/api/books/'+b).json()['status']=='ready'

def test_partial_book_hidden(client,family):
    from db import query
    f,p=family;b=dummy_book(f,p)
    query("UPDATE books SET status='failed' WHERE id=%s",(b,))
    assert client.get('/api/books/'+b).json()['pages']==[]

def test_age_adaptation():
    from ai import story_input
    b={'page_count':5,'prompt':'','snapshot':{'child':{'age':1.5}}}
    assert 'pekbok' in story_input(b)
    b['snapshot']['child']['age']=7;assert 'Gulliga' in story_input(b)
    b['snapshot']['child']['age']=11;assert 'egen läsning' in story_input(b)

def test_install_assets():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]/'static'
    m=json.loads((root/'manifest.webmanifest').read_text())
    assert m['display']=='standalone' and m['orientation']=='any'
    for icon in m['icons']:
        im=Image.open(root/icon['src'].lstrip('/'));assert str(im.width)+'x'+str(im.height)==icon['sizes']
    assert "'/api/'" in (root/'sw.js').read_text()
    assert '@media(max-width:760px)' in (root/'style.css').read_text()

def fake_ai(monkeypatch,wrong_count=False,timeout=False):
    import ai
    monkeypatch.setenv('OPENAI_API_KEY','TEST-ONLY-NOT-A-KEY')
    monkeypatch.setenv('AI_PRICING_VERIFIED','true')
    monkeypatch.setenv('IMAGE_CALL_MAX_ORE','200')
    monkeypatch.setenv('USD_SEK_CEILING','15')
    calls=[]
    buf=io.BytesIO();Image.new('RGB',(10,10),'blue').save(buf,'PNG')
    import base64
    encoded=base64.b64encode(buf.getvalue()).decode()
    class Reply:
        def __init__(self,body):self.body=body
        def raise_for_status(self):pass
        def json(self):return self.body
    class FakeClient:
        def __init__(self,*a,**k):pass
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def post(self,url,**kw):
            calls.append((url,kw))
            if timeout:raise TimeoutError('SIMULATED timeout')
            if url.endswith('/responses'):
                story={'title':'FIKTIV AI-TESTBOK','character_bible':'Tecknad testfigur i blå tröja.','pages':[{'text':'Testbarn somnar tryggt.','illustration':'En tecknad kudde.'} for _ in range(1 if wrong_count else 2)]}
                return Reply({'status':'completed','usage':{'input_tokens':200,'output_tokens':200},'output':[{'content':[{'type':'output_text','text':json.dumps(story)}]}]})
            return Reply({'usage':{'input_tokens_details':{'text_tokens':100,'image_tokens':0},'output_tokens':100},'data':[{'b64_json':encoded}]})
    monkeypatch.setattr(ai.httpx,'Client',FakeClient)
    return calls

def test_generation_exact_count_and_no_memory_write(client,family,monkeypatch):
    from db import query
    from ai import generate
    f,p=family;b=dummy_book(f,p)
    query('UPDATE budget SET committed_ore=0,limit_ore=50000 WHERE id=1')
    before=client.get('/api/families/'+f['id']).json()['memories']
    calls=fake_ai(monkeypatch);generate(b)
    result=client.get('/api/books/'+b).json()
    assert result['status']=='ready' and len(result['pages'])==2
    assert len(calls)==3
    assert client.get('/api/families/'+f['id']).json()['memories']==before
    generate(b)
    assert len(calls)==3

def test_wrong_count_stops_before_images(client,family,monkeypatch):
    from ai import generate
    f,p=family;b=dummy_book(f,p)
    calls=fake_ai(monkeypatch,wrong_count=True);generate(b)
    result=client.get('/api/books/'+b).json()
    assert result['status']=='failed' and result['pages']==[]
    assert len(calls)==1

def test_timeout_never_retries(client,family,monkeypatch):
    from ai import generate
    from db import query
    f,p=family;b=dummy_book(f,p)
    calls=fake_ai(monkeypatch,timeout=True);generate(b);generate(b)
    assert len(calls)==1
    assert client.get('/api/books/'+b).json()['status']=='failed'
    charges=query('SELECT * FROM charges WHERE book_id=%s',(b,))
    assert len(charges)==1 and charges[0]['state']=='reserved'

def test_cost_ceiling_breach_closes_budget(client,family):
    from db import query
    from ledger import reserve,settle
    f,p=family;b=dummy_book(f,p)
    cid=reserve(b,'ceiling',100)
    settle(cid,101)
    assert query('SELECT limit_ore FROM budget WHERE id=1',one=True)['limit_ore']==0
    try:reserve(b,'next',1);assert False
    except HTTPException as e:assert e.status_code==402
    query('UPDATE budget SET committed_ore=0,limit_ore=50000 WHERE id=1')

def test_worker_rejects_transaction_pooler(monkeypatch):
    import db
    monkeypatch.setenv('DATABASE_URL','postgresql://test:test@ep-test-pooler.example.invalid/test')
    try:db.connect();assert False
    except HTTPException as e:assert e.status_code==503

def test_authorized_test_mode_preserves_config_gate(monkeypatch):
    from ai import ready
    monkeypatch.setenv('OPENAI_API_KEY','TEST-ONLY')
    monkeypatch.setenv('AI_PRICING_VERIFIED','false')
    monkeypatch.setenv('AI_TEST_MODE','true')
    monkeypatch.setenv('IMAGE_CALL_MAX_ORE','5000')
    monkeypatch.setenv('USD_SEK_CEILING','15')
    assert ready()
    monkeypatch.setenv('AI_TEST_MODE','false')
    assert not ready()

def test_story_schema_requires_string_character_description():
    from ai import story_schema
    s=story_schema(4)
    assert s['properties']['character_bible']['type']=='string'
    assert s['properties']['pages']['minItems']==4
    assert s['properties']['pages']['maxItems']==4
    assert not s['additionalProperties']
