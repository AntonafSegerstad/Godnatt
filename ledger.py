import uuid
from fastapi import HTTPException
from db import connect

def reserve(book,kind,amount):
    if amount<=0: raise ValueError('Invalid cost ceiling')
    with connect() as c:
        b=c.execute('SELECT * FROM budget WHERE id=1 FOR UPDATE').fetchone()
        if c.execute('SELECT id FROM charges WHERE book_id=%s AND kind=%s',(book,kind)).fetchone():
            raise HTTPException(409,'Detta AI-anrop har redan startats. Ingen automatisk omkörning görs.')
        if b['committed_ore']+amount>b['limit_ore']:
            raise HTTPException(402,'AI-budgeten räcker inte. Inga nya anrop har startats.')
        id=str(uuid.uuid4())
        c.execute('UPDATE budget SET committed_ore=committed_ore+%s WHERE id=1',(amount,))
        c.execute('INSERT INTO charges(id,book_id,kind,reserved_ore) VALUES(%s,%s,%s,%s)',(id,book,kind,amount))
        return id

def settle(id,actual):
    with connect() as c:
        c.execute('SELECT id FROM budget WHERE id=1 FOR UPDATE')
        charge=c.execute('SELECT * FROM charges WHERE id=%s FOR UPDATE',(id,)).fetchone()
        if charge['state']!='reserved':return
        if actual is None:return
        if actual<0:raise ValueError('Invalid cost')
        if actual>charge['reserved_ore']:
            c.execute('UPDATE budget SET limit_ore=0 WHERE id=1')
            c.execute("UPDATE charges SET state='review',actual_ore=%s WHERE id=%s",(actual,id))
            return
        c.execute('UPDATE budget SET committed_ore=committed_ore-%s WHERE id=1',(charge['reserved_ore']-actual,))
        c.execute("UPDATE charges SET actual_ore=%s,state='settled' WHERE id=%s",(actual,id))
