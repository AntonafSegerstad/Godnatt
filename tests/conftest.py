import os,sys,uuid
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

@pytest.fixture(scope='session')
def database():
    url=os.getenv('TEST_DATABASE_URL')
    if not url:pytest.skip('TEST_DATABASE_URL saknas: verkliga PostgreSQL-tester kräver separat testdatabas.')
    import psycopg
    from psycopg.conninfo import make_conninfo
    schema='test_'+uuid.uuid4().hex
    with psycopg.connect(url,autocommit=True) as c:c.execute(f'CREATE SCHEMA {schema}')
    os.environ['DATABASE_URL']=make_conninfo(url,options=f'-c search_path={schema}')
    import db
    db.init()
    yield
    with psycopg.connect(url,autocommit=True) as c:c.execute(f'DROP SCHEMA {schema} CASCADE')

@pytest.fixture
def client(database):
    from fastapi.testclient import TestClient
    import app
    # Deliberately no lifespan: do not launch unrelated recovery threads in tests.
    return TestClient(app.app,raise_server_exceptions=False,base_url='https://testserver')

@pytest.fixture
def family(client):
    f=client.post('/api/families',json={'name':'FIKTIV TESTFAMILJ','pin':'1234'}).json()
    p=client.post(f'/api/families/{f["id"]}/people',json={'name':'Testbarn','age':1.5,'gender':''}).json()
    return f,p
