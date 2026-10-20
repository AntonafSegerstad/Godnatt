const {chromium,webkit}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..','static');
(async()=>{for(const [engine,launcher]of Object.entries({chromium,webkit})){
const browser=await launcher.launch({headless:true});const page=await browser.newPage({viewport:{width:390,height:844}});
const f={id:'f',name:'Fiktiv familj',people:[],memories:[],relations:[],books:[{id:'b',title:'Fiktiv bok',status:'ready',page_count:1,created_at:'2026-10-20'}]};let creates=0,uploads=0,deletes=0;
await page.route('**/*',async route=>{
const req=route.request(),url=new URL(req.url()),p=url.pathname;let data,type='application/json',status=200;
if(p==='/api/status')data={database:true};
else if(p==='/api/budget')data={committed_ore:0,limit_ore:50000};
else if(p==='/api/families')data=[{id:f.id,name:f.name}];
else if(p==='/api/families/f')data=f;
else if(p==='/api/families/f/people'){creates++;data={id:'p',...req.postDataJSON()};f.people=[data];}
else if(p==='/api/people/p'){data={id:'p',...req.postDataJSON()};f.people=[data];}
else if(p==='/api/people/p/photo'){uploads++;if(uploads===1){status=503;data={detail:'Fiktivt bildfel'};}else{data={photo_id:'img'};f.people[0].photo_id='img';}}
else if(p==='/api/books/b'&&req.method()==='DELETE'){deletes++;f.books=[];data={ok:true};}
else if(p.startsWith('/api/')){await route.abort();return;}
else{const file=p==='/'?'index.html':p.slice(1);if(!['index.html','app.js','style.css','logo.svg'].includes(file)){await route.abort();return;}data=fs.readFileSync(path.join(root,file),'utf8');type=file.endsWith('.js')?'application/javascript':file.endsWith('.css')?'text/css':file.endsWith('.svg')?'image/svg+xml':'text/html';}
await route.fulfill({status,contentType:type,body:typeof data==='string'?data:JSON.stringify(data)});
});
await page.goto('https://test.invalid/');await page.waitForSelector('#welcome-family');assert.equal(await page.locator('#content').count(),0);
await page.selectOption('#welcome-family','f');await page.getByRole('button',{name:'Öppna familjen'}).click();
page.on('dialog',d=>d.accept());await page.getByRole('button',{name:'Ta bort Fiktiv bok',exact:true}).click();await page.waitForFunction(()=>!document.querySelector('[data-delete-book]'));assert.equal(deletes,1);
await page.getByRole('button',{name:'Personer',exact:true}).click();await page.getByRole('button',{name:'Lägg till person ＋'}).click();
await page.locator('[name=name]').fill('Fiktiv person');await page.locator('[name=age]').fill('7');await page.locator('[name=general_info]').fill('Tycker om böcker');
await page.locator('#person-photo').setInputFiles({name:'fiktiv.png',mimeType:'image/png',buffer:Buffer.from('fiktiv bild')});
await page.getByRole('button',{name:'Skapa person',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#person-photo-status').textContent.includes('kunde inte'));
await page.getByRole('button',{name:'Skapa person',exact:true}).click();await page.waitForFunction(()=>!document.querySelector('dialog').open);
assert.equal(creates,1);assert.equal(uploads,2);assert.equal(f.people[0].photo_id,'img');
await page.getByRole('button',{name:'← Välj familj'}).click();await page.waitForSelector('#welcome-family');
console.log(engine+': PASS family selection, book delete, photo on create, retry without duplicate');await browser.close();
}})().catch(e=>{console.error(e);process.exitCode=1});
