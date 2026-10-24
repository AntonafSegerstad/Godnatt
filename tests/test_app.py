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
    foreign=client.post('/api/families',json={'name':'ANNAN TESTFAMILJ','pin':'1234'}).json()
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
    assert client.post('/api/families',json={'name':'bad','pin':'1234'},headers={'origin':'https://other.example'}).status_code==403
    assert client.post('/api/families',json={'name':'good','pin':'1234'},headers={'origin':'https://testserver'}).status_code==201

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
    second=TestClient(app,base_url='https://testserver')
    assert second.post('/api/families/'+f['id']+'/unlock',json={'pin':'1234'}).status_code==200
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
    from ai import story_input,page_limits,story_schema
    b={'page_count':5,'prompt':'Ett mysterium','snapshot':{'child':{'age':1.5},'people':[{'age':40}]}}
    limits=[]
    for age in [1.5,4,5,7,8,11,12,16]:
        b['snapshot']['child']['age']=age
        payload=json.loads(story_input(b))
        assert f'aktuella ålder är {float(age)} år' in payload['instruction']
        assert payload['context']==b['snapshot']
        assert payload['order']==b['prompt']
        words,chars=page_limits(age);limits.append(words)
        assert story_schema(5,age)['properties']['pages']['items']['properties']['text']['maxLength']==chars
    assert limits==sorted(set(limits))


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
    s=story_schema(4,11)
    assert s['properties']['character_bible']['type']=='string'
    assert s['properties']['pages']['minItems']==4
    assert s['properties']['pages']['maxItems']==4
    assert not s['additionalProperties']

def test_general_info_single_field_preserves_origin(client,family):
    from db import query
    f,p=family
    body={'name':p['name'],'age':1.5,'general_info':'Tycker om katter'}
    assert client.put('/api/people/'+p['id'],json=body).status_code==200
    first=client.get('/api/families/'+f['id']).json()['memories'][0]
    body['general_info']='Tycker om katter och böcker'
    client.put('/api/people/'+p['id'],json=body)
    ms=client.get('/api/families/'+f['id']).json()['memories']
    assert len(ms)==1 and ms[0]['kind']=='profile'
    assert ms[0]['text']==body['general_info']
    assert ms[0]['original_text']=='Tycker om katter' and ms[0]['created_at']==first['created_at']
    body['general_info']=''
    assert client.put('/api/people/'+p['id'],json=body).status_code==200
    created=client.post('/api/families/'+f['id']+'/people',json={'name':'Ny','age':7,'general_info':'Dansar'}).json()
    assert query("SELECT text FROM memories WHERE person_id=%s AND kind='profile'",(created['id'],),True)['text']=='Dansar'

def test_delete_family_preserves_costs_and_other_families(client,family):
    from db import query
    from ledger import reserve,settle
    from ai import save_media
    f,p=family;b=dummy_book(f,p)
    cid=reserve(b,'deletion-test',100);settle(cid,12)
    assert client.delete('/api/families/'+f['id']).status_code==409
    buf=io.BytesIO();Image.new('RGB',(8,8),'green').save(buf,'PNG');mid=save_media(buf.getvalue())
    query('INSERT INTO pages(book_id,number,text,image_id) VALUES(%s,1,%s,%s)',(b,'Test',mid))
    query("UPDATE books SET status='ready' WHERE id=%s",(b,))
    other=client.post('/api/families',json={'name':'Behåll familjen','pin':'1234'}).json()
    before=client.get('/api/budget').json()
    assert client.delete('/api/families/'+f['id']).status_code==200
    assert client.get('/api/families/'+f['id']).status_code==404
    assert client.get('/api/books/'+b).status_code==404
    assert client.get('/api/media/'+mid).status_code==404
    assert client.get('/api/families/'+other['id']).status_code==200
    assert client.get('/api/budget').json()['committed_ore']==before['committed_ore']
    charge=query('SELECT * FROM charges WHERE id=%s',(cid,),True)
    assert charge['book_id'] is None and charge['actual_ore']==12

def test_toddler_overlong_text_stops_before_images(client,family,monkeypatch):
    from ai import generate
    f,p=family;b=dummy_book(f,p)
    calls=fake_ai(monkeypatch)
    import ai
    original=ai.page_limits
    monkeypatch.setattr(ai,'page_limits',lambda age:(2,120))
    generate(b)
    assert client.get('/api/books/'+b).json()['status']=='failed'
    assert len(calls)==1

def test_delete_book_keeps_budget_and_other_book(client,family):
    from db import query
    from ledger import reserve,settle
    from ai import save_media
    f,p=family;b=dummy_book(f,p);other=dummy_book(f,p)
    cid=reserve(b,'delete-book',100);settle(cid,7)
    assert client.delete('/api/books/'+b).status_code==409
    buf=io.BytesIO();Image.new('RGB',(8,8),'blue').save(buf,'PNG');mid=save_media(buf.getvalue())
    for bid in [b,other]:
        query('INSERT INTO pages(book_id,number,text,image_id) VALUES(%s,1,%s,%s)',(bid,'Fiktiv',mid))
        query("UPDATE books SET status='ready' WHERE id=%s",(bid,))
    before=client.get('/api/budget').json()
    assert client.delete('/api/books/'+b).status_code==200
    assert client.get('/api/books/'+b).status_code==404
    assert client.get('/api/books/'+other).status_code==200
    assert client.get('/api/media/'+mid).status_code==200
    assert client.get('/api/budget').json()['committed_ore']==before['committed_ore']
    assert query('SELECT book_id FROM charges WHERE id=%s',(cid,),True)['book_id'] is None
    assert client.delete('/api/books/'+other).status_code==200
    assert client.get('/api/media/'+mid).status_code==404

def test_family_pin_protects_content_and_media(client,family):
    from fastapi.testclient import TestClient
    from app import app
    from db import query
    f,p=family
    stranger=TestClient(app,base_url='https://testserver')
    assert stranger.get('/api/families/'+f['id']).status_code==401
    assert stranger.put('/api/people/'+p['id'],json={'name':'Ändra','age':7}).status_code==401
    listed=stranger.get('/api/families').json()
    assert not any('pin_hash' in row or 'pin_setup_hash' in row for row in listed)
    assert stranger.post('/api/families/'+f['id']+'/unlock',json={'pin':'0000'}).status_code==401
    response=stranger.post('/api/families/'+f['id']+'/unlock',json={'pin':'1234'})
    assert response.status_code==200
    assert 'HttpOnly' in response.headers['set-cookie'] and 'Secure' in response.headers['set-cookie']
    assert stranger.get('/api/families/'+f['id']).status_code==200
    stored=query('SELECT pin_hash FROM families WHERE id=%s',(f['id'],),True)['pin_hash']
    assert stored!='1234'
    buf=io.BytesIO();Image.new('RGB',(8,8),'green').save(buf,'PNG')
    mid=client.post('/api/people/'+p['id']+'/photo',files={'file':('test.png',buf.getvalue(),'image/png')}).json()['photo_id']
    outsider=TestClient(app,base_url='https://testserver')
    assert outsider.get('/api/media/'+mid).status_code==401
    assert stranger.get('/api/media/'+mid).status_code==200
    b=dummy_book(f,p)
    assert outsider.get('/api/books/'+b).status_code==401
    assert outsider.delete('/api/books/'+b).status_code==401
    assert outsider.delete('/api/families/'+f['id']).status_code==401

def test_pin_attempt_limit_and_setup_link(client,family):
    from fastapi.testclient import TestClient
    from app import app
    from db import query
    from access import digest
    f,p=family
    stranger=TestClient(app,base_url='https://testserver')
    for _ in range(5):assert stranger.post('/api/families/'+f['id']+'/unlock',json={'pin':'0000'}).status_code==401
    assert stranger.post('/api/families/'+f['id']+'/unlock',json={'pin':'1234'}).status_code==429
    legacy=str(uuid.uuid4());token='one-time-test-token-of-sufficient-length'
    query('INSERT INTO families(id,name,pin_setup_hash) VALUES(%s,%s,%s)',(legacy,'TEST LEGACY',digest(token)))
    assert stranger.get('/api/families/'+legacy).status_code==401
    assert stranger.post('/api/families/'+legacy+'/pin-setup',json={'token':'wrong-token-of-sufficient-length-123','pin':'9876'}).status_code==403
    assert stranger.post('/api/families/'+legacy+'/pin-setup',json={'token':token,'pin':'9876'}).status_code==200
    assert stranger.post('/api/families/'+legacy+'/pin-setup',json={'token':token,'pin':'9876'}).status_code==403
    assert stranger.get('/api/families/'+legacy).status_code==200
    assert client.post('/api/families',json={'name':'No PIN'}).status_code==422
    assert client.post('/api/families',json={'name':'Short PIN','pin':'123'}).status_code==422


def test_age_and_scene_reach_actual_image_requests(client,family,monkeypatch):
    from ai import generate
    from db import query
    f,p=family
    for age in [1.5,7,16]:
        person=dict(p,age=age)
        b=dummy_book(f,person)
        calls=fake_ai(monkeypatch);generate(b)
        assert client.get('/api/books/'+b).json()['status']=='ready'
        assert len(calls)==3
        text_request=calls[0][1]['json']
        instruction=json.loads(text_request['input'])['instruction']
        assert f'aktuella ålder är {float(age)} år' in instruction
        for number,(_,kwargs) in enumerate(calls[1:],1):
            image_request=kwargs['json']
            prompt=image_request['prompt']
            assert f'huvudperson som är {float(age)} år' in prompt
            assert f'Scen {number}: En tecknad kudde.' in prompt
            assert 'Tecknad testfigur i blå tröja.' in prompt
            assert 'Testbarn somnar tryggt.' in prompt
            assert 'Enkel handmålad 2D-barnboksillustration i varma dämpade pastellfärger' not in prompt
            assert image_request['size']=='1024x1024' and image_request['quality']=='low'


def test_image_prompt_preserves_book_style_and_distinct_scenes():
    from ai import illustration_input
    book={'snapshot':{'child':{'age':16}}}
    story={'character_bible':'Grafisk tusch med djupa blå skuggor; Sam har lockigt hår och röd jacka.'}
    a=illustration_input(book,story,{'text':'Sam hittar en hemlig dörr.','illustration':'Nattlig stad, dörren lyser.'},1,['Sam'])
    b=illustration_input(book,story,{'text':'Sam kliver in.','illustration':'En svävande skog bakom dörren.'},2,['Sam'])
    assert story['character_bible'] in a and story['character_bible'] in b
    assert 'Nattlig stad' in a and 'svävande skog' in b and a!=b
    assert 'Fotoreferenser i ordning: Sam' in a


def test_provider_error_identifies_stage_without_disclosing_response():
    import httpx
    from ai import provider_result
    response=httpx.Response(400,request=httpx.Request('POST','https://api.openai.com/v1/responses'),
                            json={'error':{'code':'invalid_json_schema','message':'PRIVATE INPUT MUST NOT BE SHOWN'}})
    try:
        provider_result(response,'Textgenereringen')
        assert False
    except ValueError as error:
        message=str(error)
        assert 'Textgenereringen' in message and 'HTTP 400' in message and 'svarsformat' in message
        assert 'PRIVATE' not in message
