// Cloud-only layout investigation. No live family data or paid AI calls.
const {chromium,webkit,firefox}=require('playwright');
const fs=require('fs'),path=require('path'),cp=require('child_process');
const root=path.resolve(__dirname,'..');
const sources=revision=>Object.fromEntries(['index.html','app.js','style.css'].map(file=>[file,revision?cp.execFileSync('git',['show',revision+':static/'+file],{cwd:root,encoding:'utf8'}):fs.readFileSync(path.join(root,'static',file),'utf8')]));
const current=sources(),old=sources('5ce8a9e43761b5cfae74110ac7ba3863e307056a');
const text='Det här är en fiktiv berättelse för att kontrollera läsytan. '.repeat(24);
const image='<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024"><rect width="1024" height="1024" fill="#d1b797"/><circle cx="512" cy="512" r="300" fill="#bb8574"/></svg>';
const results=[];
async function check(browser,engine,source,label,width,height,dpr,scale=1,bigText=false,toddler=false){
 const context=await browser.newContext({viewport:{width,height},deviceScaleFactor:dpr});
 await context.route('**/*',async route=>{
 const p=new URL(route.request().url()).pathname;
 let body,type='application/json';
 if(p==='/api/status')body={database:true};
 else if(p==='/api/budget')body={committed_ore:0,limit_ore:50000};
 else if(p==='/api/books/test')body={id:'test',status:'ready',family_id:'test',title:'Fiktivt layouttest',page_count:2,snapshot:{child:{name:'Test',age:toddler?1.5:11}},pages:[{image_id:'image',text:toddler?'En liten boll.':text},{image_id:'image',text:'Slut.'}]};
 else if(p==='/api/media/image'){body=image;type='image/svg+xml'}
 else if(p==='/book/test'){body=source['index.html'];type='text/html'}
 else if(p==='/app.js'){body=source['app.js'];type='application/javascript'}
 else if(p==='/style.css'){body=source['style.css'];type='text/css'}
 else {await route.abort();return;}
 await route.fulfill({status:200,contentType:type,body:typeof body==='string'?body:JSON.stringify(body)});
 });
 const page=await context.newPage();await page.goto('https://layout.test/book/test');await page.waitForSelector('.reader');await page.locator('.spread img').evaluate(img=>img.decode());
 if(scale!==1)await page.addStyleTag({content:`html{zoom:${scale}}`});
 if(bigText)await page.addStyleTag({content:'.page-text p{font-size:48px!important}'});
 const geometry=await page.evaluate(()=>{
 const rect=s=>{const r=document.querySelector(s).getBoundingClientRect();return {left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height}};
 const img=rect('.spread img'),panel=document.querySelector('.page-image')?rect('.page-image'):img,txt=rect('.page-text'),nav=rect('.reader-nav');
 const overlap=Math.min(panel.right,txt.right)-Math.max(panel.left,txt.left)>1&&Math.min(panel.bottom,txt.bottom)-Math.max(panel.top,txt.top)>1;
 const el=document.querySelector('.page-text');el.scrollTop=el.scrollHeight;
 return {overlap,img,panel,txt,nav,allTextReachable:el.scrollHeight-el.scrollTop<=el.clientHeight+1,navVisible:nav.bottom<=innerHeight+1&&nav.top>=0};
 });
 results.push({engine,label,width,height,dpr,scale,bigText,toddler,...geometry});
 if(label==='current'&&width===390&&height===844&&scale===1&&!bigText&&!toddler)await page.screenshot({path:'/tmp/godnatt-'+engine+'.png'});
 await context.close();
}
(async()=>{
 for(const [engine,launcher]of Object.entries({chromium,webkit,firefox})){
 let browser;try{browser=await launcher.launch({headless:true});}catch(e){console.log(engine,'UNAVAILABLE',e.message.split('\n')[0]);continue;}
 for(const [w,h,dpr]of [[390,844,3],[412,915,2.625],[768,1024,2],[820,1180,2],[1440,900,1],[320,568,2]]){
  for(const [width,height]of [[w,h],[h,w]])await check(browser,engine,current,'current',width,height,dpr);
 }
 for(const scale of [1.25,1.5,2])await check(browser,engine,current,'current',390,844,3,scale);
 await check(browser,engine,current,'current',390,844,3,1,true);
 await check(browser,engine,current,'current',390,844,3,1,false,true);
 await check(browser,engine,old,'old',390,844,3);
 await browser.close();
 }
 fs.writeFileSync(path.join(root,'qa/layout-results.json'),JSON.stringify(results,null,2));
 console.log(JSON.stringify(results.map(({engine,label,width,height,scale,bigText,toddler,overlap,navVisible,allTextReachable})=>({engine,label,width,height,scale,bigText,toddler,overlap,navVisible,allTextReachable})),null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
