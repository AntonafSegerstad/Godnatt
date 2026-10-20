'use strict';
const $=s=>document.querySelector(s), app=$('#app'), dialog=$('#dialog');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let family=null,tab='books',person=null,page=0,book=null,poller=null,installPrompt=null;
let pending=new Map(),saveChain=Promise.resolve(),saving=0;
const today=()=>new Date().toLocaleDateString('sv-SE');
const date=s=>new Date(s).toLocaleDateString('sv-SE');
async function api(url,method='GET',data){
 const options={method};
 if(data instanceof FormData)options.body=data;
 else if(data!==undefined){options.headers={'Content-Type':'application/json'};options.body=JSON.stringify(data);}
 const r=await fetch('/api'+url,options);
 const b=await r.json().catch(()=>({detail:'Tjänsten svarar inte.'}));
 if(!r.ok)throw Error(typeof b.detail==='string'?b.detail:'Kontrollera uppgifterna och försök igen.');
 return b;
}
function toast(s){$('#toast').textContent=s;$('#toast').style.display='block';setTimeout(()=>$('#toast').style.display='none',5500);}
function modal(html){$('#dialog-body').innerHTML=html;dialog.showModal();}
function avatar(p){return p.photo_id?'<img class="avatar" src="/api/media/'+esc(p.photo_id)+'" alt="'+esc(p.name)+'">':'<span class="avatar">'+esc(p.name.slice(0,1))+'</span>';}
async function budget(){try{const b=await api('/budget');$('#budget').textContent='AI-budget: '+(b.committed_ore/100).toFixed(2)+' kr använt eller reserverat · högst '+(b.limit_ore/100).toFixed(0)+' kr';}catch{}}
async function start(){
 try{
 const status=await api('/status');
 if(!status.database){app.innerHTML='<div class="hero"><div><p class="eyebrow">Personliga små böcker</p><h1>En saga som<br>är alldeles din.</h1><p>Godnatt väntar på sin databas. Inget innehåll sparas på denna enhet.</p></div>'+night()+'</div><p class="notice">Serveranslutningen behöver göras klar innan familjer och böcker kan sparas.</p>';return;}
 if(location.pathname.startsWith('/book/')){await readBook(location.pathname.split('/')[2]);return;}
 const fs=await api('/families');const selected=localStorage.getItem('godnatt-family');
 if(fs.length){await selectFamily(fs.find(f=>f.id===selected)?.id||fs[0].id);return;}
 app.innerHTML='<section class="hero"><div><p class="eyebrow">Godnatt, stora lilla världen</p><h1>En saga som<br>är alldeles din.</h1><p>Små ögonblick blir stora äventyr. Skapa personliga böcker om barnen och deras värld.</p><button data-action="new-family">Skapa din första familj ＋</button></div></section><p class="muted">Inga konton. Alla familjer är öppna för alla.</p>';
 }catch(e){app.innerHTML='<h1>En liten paus</h1><p>'+esc(e.message)+'</p><button data-action="reload">Försök igen</button>';}
 budget();
}
function night(){return '<div class="night" aria-hidden="true"><span class="bigmoon">●</span><span class="star">✧ · ✦</span><span class="bookicon">📖</span><div class="hills"></div><div class="hills hill2"></div></div>';}
async function selectFamily(id){document.body.classList.remove('reading');book=null;await flush();family=await api('/families/'+id);localStorage.setItem('godnatt-family',id);history.replaceState({},'','/');person=null;await renderHome();budget();}
async function renderHome(){
 clearTimeout(poller);
 const fs=await api('/families');
 app.innerHTML='<div class="row between"><div class="row"><span class="eyebrow">Din sagovärld</span><select id="family-select" aria-label="Välj familj">'+fs.map(f=>'<option value="'+esc(f.id)+'" '+(f.id===family.id?'selected':'')+'>'+esc(f.name)+'</option>').join('')+'</select></div><div class="row"><button class="quiet small" data-action="new-family">Ny familj ＋</button><button class="quiet small danger" data-action="delete-family">Ta bort familj</button></div></div><section class="hero"><div><p class="eyebrow">För dagens sista lilla äventyr</p><h1>Vad ska vi<br>drömma om i kväll?</h1><p class="muted">En bekant hand. En modig liten hjälte. En berättelse där ditt barn hör hemma.</p></div></section><div class="tabs"><button data-tab="books" class="'+(tab==='books'?'active':'')+'">Bokhyllan</button><button data-tab="people" class="'+(tab==='people'?'active':'')+'">Personer</button></div><div id="content"></div>';
 $('#family-select').onchange=e=>selectFamily(e.target.value).catch(e=>toast(e.message));
 renderContent();
 if(family.books.some(b=>['queued','generating'].includes(b.status)))poller=setTimeout(async()=>{try{family=await api('/families/'+family.id);if(!dialog.open)renderContent();budget();poller=setTimeout(()=>refresh(),5000);}catch{}},5000);
}
async function refresh(){if(!family||person||dialog.open)return;family=await api('/families/'+family.id);renderContent();if(family.books.some(b=>['queued','generating'].includes(b.status)))poller=setTimeout(refresh,5000);budget();}
function renderContent(){
 if(tab==='people'){
 $('#content').innerHTML='<div class="row between"><h2>Alla som hör till</h2><button class="quiet" data-action="add-person">Lägg till person ＋</button></div><div class="grid">'+family.people.map(p=>'<button class="card person quiet" data-person="'+esc(p.id)+'">'+avatar(p)+'<div><h3>'+esc(p.name)+'</h3><small>'+esc(p.age)+' år</small></div></button>').join('')+'</div>'+(!family.people.length?'<p class="empty">Lägg till ett barn, en vuxen eller en kompis.</p>':'');
 return;
 }
 $('#content').innerHTML='<div class="row between"><h2>Era små äventyr</h2><div class="row"><span class="muted">'+family.books.length+' böcker</span><button data-action="new-book">Ny bok ＋</button></div></div>'+(family.books.length?'<div class="grid">'+family.books.map(b=>'<article class="card bookcard"><div class="cover">'+(b.cover&&b.status==='ready'?'<img src="/api/media/'+esc(b.cover)+'" alt="">':b.status==='failed'?'☁':'☾')+'</div><span class="eyebrow">'+date(b.created_at)+' · '+b.page_count+' sidor</span><h3>'+esc(b.title)+'</h3>'+(b.status==='ready'?'<p class="pill">Boken är klar</p><p><a class="button" href="/book/'+esc(b.id)+'">Läs boken ↗</a></p>':b.status==='failed'?'<p>'+esc(b.error)+'</p><button class="quiet" data-action="new-book">Ny beställning</button>':'<p><span class="spinner"></span> Skapar · '+b.progress+'/'+b.page_count+' bilder klara</p>')+'</article>').join('')+'</div>':'<div class="empty"><h3>Plats för er första saga.</h3><p>Alla färdiga böcker sparas här.</p><button data-action="new-book">Skapa en bok</button></div>');
}
function personForm(p=null){
 const info=family.memories.find(m=>m.person_id===p?.id&&m.kind==='profile')?.text||'';
 modal('<h2>'+(p?'Redigera person':'En ny person')+'</h2><form id="person-form"><label>Namn<input name="name" required maxlength="100" value="'+esc(p?.name)+'"></label><div class="cols"><label>Ålder i år<input name="age" type="number" min="0" max="120" step="0.1" required placeholder="1,5" value="'+esc(p?.age??'')+'"></label><label>Kön<input name="gender" maxlength="50" value="'+esc(p?.gender)+'" placeholder="Valfritt"></label></div><label>Allmän info om personen<textarea name="general_info" maxlength="5000" placeholder="Personlighet, intressen, viktiga personer och annat som är bra att veta…">'+esc(info)+'</textarea></label><p><button>Spara person</button></p></form>');
 $('#person-form').onsubmit=async e=>{e.preventDefault();await submit(e.target,async()=>{const d=Object.fromEntries(new FormData(e.target));d.age=Number(d.age);await api(p?'/people/'+p.id:'/families/'+family.id+'/people',p?'PUT':'POST',d);dialog.close();family=await api('/families/'+family.id);if(p)showPerson(p.id);else renderContent();});};
}
async function showPerson(id){
 await flush();family=await api('/families/'+family.id);person=family.people.find(p=>p.id===id);const p=person;if(!p)return;
 clearTimeout(poller);
 const profile=family.memories.find(m=>m.person_id===id&&m.kind==='profile');
 const memories=family.memories.filter(m=>m.person_id===id&&m.kind!=='profile'),relations=family.relations.filter(r=>r.source_id===id||r.target_id===id);
 app.innerHTML='<button class="quiet small" data-action="home">← Familjen</button><div class="row between"><div class="row">'+avatar(p)+'<h1>'+esc(p.name)+'</h1><span class="pill">'+esc(p.age)+' år</span></div><button class="quiet" data-action="edit-person">Redigera</button></div><div class="cols"><section class="card"><h2>Vem är '+esc(p.name)+'?</h2><p class="muted">Fyll på när du vill. Texten sparas automatiskt.</p><label>Allmän info om personen<textarea id="general-info" maxlength="5000" placeholder="Personlighet, intressen och annat som är bra att veta…">'+esc(profile?.text)+'</textarea></label><div class="autosave" id="info-save"></div><label>Personfoto<input id="photo" type="file" accept="image/png,image/jpeg,image/webp"></label><p class="muted">Används som referens för tecknade bilder.</p>'+(p.photo_id?'<button class="quiet small" data-action="remove-photo">Ta bort foto</button>':'')+'</section><section class="card"><div class="row between"><h2>Relationer</h2><button class="quiet small" data-action="relation">Lägg till</button></div>'+relations.map(r=>'<div class="relation">'+esc(name(r.source_id))+' är <strong>'+esc(r.role)+'</strong> till '+esc(name(r.target_id))+' <button class="quiet small danger" data-remove-relation="'+esc(r.id)+'" aria-label="Ta bort relation">✕</button></div>').join('')+(!relations.length?'<p class="muted">Knyt roller till rätt personer. Samma person kan ha flera roller.</p>':'')+'</section></div>'+(memories.length?'<details><summary>Tidigare sparade uppgifter</summary>'+memories.map(memoryCard).join('')+'</details>':'')+'<p><button class="quiet danger" data-action="delete-person">Ta bort '+esc(p.name)+'</button></p>';
 $('#general-info').oninput=e=>{const general_info=e.target.value;queueSave('profile:'+id,()=>api('/people/'+id,'PUT',{name:p.name,age:Number(p.age),gender:p.gender,general_info}),'#info-save');};
 $('#photo').onchange=async e=>{if(!e.target.files[0])return;const f=new FormData();f.append('file',e.target.files[0]);try{await api('/people/'+id+'/photo','POST',f);await showPerson(id);toast('Fotot är sparat.');}catch(e){toast(e.message);}};
}
function name(id){return family.people.find(p=>p.id===id)?.name||'Borttagen person';}
function memoryCard(m){return '<div class="timeline"><span class="eyebrow">'+esc(m.event_date)+'</span><p>'+esc(m.text)+'</p><div class="row"><button class="quiet small" data-edit-memory="'+esc(m.id)+'">Rätta</button><button class="quiet small danger" data-delete-memory="'+esc(m.id)+'">Radera</button></div></div>';}
function queueSave(key,fn,status){
 const old=pending.get(key);if(old)clearTimeout(old.timer);
 $(status)&&( $(status).textContent='Sparar…');
 const task={fn,status};task.timer=setTimeout(()=>runSave(key),700);pending.set(key,task);
}
function runSave(key){
 const task=pending.get(key);if(!task)return saveChain;clearTimeout(task.timer);pending.delete(key);
 saving++; saveChain=saveChain.catch(()=>{}).then(task.fn).then(()=>{if($(task.status))$(task.status).textContent='Sparat ✓';}).catch(e=>{if(!pending.has(key))pending.set(key,task);if($(task.status))$(task.status).textContent='Kunde inte spara. Texten finns kvar här.';toast(e.message);throw e;}).finally(()=>saving--);
 // Preserve rejection for flush; next edit may recover without losing the previous text.
 saveChain.catch(()=>{});
 return saveChain;
}
async function flush(){for(const key of [...pending.keys()])runSave(key);await saveChain;}
function relationForm(){
 if(family.people.length<2){toast('Lägg till minst två personer.');return;}
 const opts=family.people.map(p=>'<option value="'+esc(p.id)+'">'+esc(p.name)+'</option>').join('');
 modal('<h2>Knyt ihop personerna</h2><form id="relation-form"><label>Person<select name="source_id">'+opts+'</select></label><label>Är<input name="role" required placeholder="pappa, bonusmamma, kompis…" maxlength="80"></label><label>Till<select name="target_id">'+opts+'</select></label><p><button>Spara relation</button></p></form>');
 $('#relation-form').elements.source_id.value=person.id;$('#relation-form').elements.target_id.value=family.people.find(p=>p.id!==person.id).id;
 $('#relation-form').onsubmit=async e=>{e.preventDefault();await submit(e.target,async()=>{await api('/families/'+family.id+'/relations','POST',Object.fromEntries(new FormData(e.target)));dialog.close();showPerson(person.id);});};
}
async function newBook(){
 await flush();family=await api('/families/'+family.id);
 if(!family.people.length){personForm();toast('Lägg först till barnet som boken ska handla om.');return;}
 person=null;clearTimeout(poller);
 app.innerHTML='<button class="quiet small" data-action="home">← Bokhyllan</button><div class="formbox"><p class="eyebrow">Ett nytt litet äventyr</p><h1>Vems saga blir det?</h1><form id="book-form"><div class="cols"><label>Huvudperson<select name="person_id" id="child">'+family.people.map(p=>'<option value="'+esc(p.id)+'">'+esc(p.name)+' · '+esc(p.age)+' år</option>').join('')+'</select></label><label>Antal sidor<input name="page_count" type="number" min="1" max="20" value="5" required></label></div><label>Vad ska sagan handla om?<textarea name="prompt" maxlength="5000" placeholder="Mormor hälsade på, lagade pannkakor och lekte i sandlådan…"></textarea></label><p class="muted">Lämna tomt så får sparade minnen ge sagan liv. Språk och bilder anpassas efter åldern.</p><h2>Det vi vet om huvudpersonen</h2><p class="muted">Du kan rätta texten här. Datum och ursprung sparas. Ändringar sparas automatiskt.</p><div id="context"></div><p><button id="create">Skapa boken ✧</button></p><p id="order-status" role="status"></p></form></div>';
 function contexts(){const id=$('#child').value;const ms=family.memories.filter(m=>m.person_id===id&&m.text.trim());$('#context').innerHTML=ms.map(m=>'<label>'+esc(m.event_date)+'<textarea data-context="'+esc(m.id)+'" maxlength="5000">'+esc(m.text)+'</textarea></label><div class="autosave" id="save-'+esc(m.id)+'"></div>').join('')||'<p class="notice">Inga minnen ännu. Lägg till dem under Personer, eller skriv ett ämne ovan.</p>';document.querySelectorAll('[data-context]').forEach(el=>el.oninput=()=>{const m=ms.find(m=>m.id===el.dataset.context);const text=el.value;queueSave(m.id,()=>api('/memories/'+m.id,'PUT',{text,event_date:m.event_date}),'#save-'+m.id);});}
 contexts();$('#child').onchange=async()=>{try{await flush();family=await api('/families/'+family.id);contexts();}catch(e){toast(e.message);}};
 const requestKey=crypto.randomUUID();
 $('#book-form').onsubmit=async e=>{e.preventDefault();await submit(e.target,async()=>{await flush();$('#order-status').textContent='Beställer din bok…';const d=Object.fromEntries(new FormData(e.target));d.page_count=Number(d.page_count);d.request_key=requestKey;const b=await api('/families/'+family.id+'/books','POST',d);await readBook(b.id);});};
}
async function readBook(id){
 clearTimeout(poller);book=await api('/books/'+id);history.replaceState({},'','/book/'+id);
 if(book.status!=='ready'){
 app.innerHTML='<div class="formbox"><button class="quiet" data-return-family="'+esc(book.family_id)+'">← Bokhyllan</button><h1>'+esc(book.status==='failed'?'Boken blev inte klar':'En saga tar form…')+'</h1>'+(book.status==='failed'?'<p class="notice">'+esc(book.error)+'</p>':'<p><span class="spinner"></span> '+book.progress+' av '+book.page_count+' bilder klara.</p><p>Du kan lämna sidan. Boken sparas under familjen.</p>')+'</div>';
 if(book.status!=='failed')poller=setTimeout(()=>readBook(id).catch(e=>toast(e.message)),4000);budget();return;
 }
 page=Math.min(page,book.pages.length-1);renderReader();budget();
}
function renderReader(){
 const p=book.pages[page];
 document.body.classList.add('reading');
 app.innerHTML='<article class="reader" aria-label="'+esc(book.title)+'"><button class="reader-close quiet" data-return-family="'+esc(book.family_id)+'" aria-label="Stäng boken">✕</button><div class="spread" id="spread"><img src="/api/media/'+esc(p.image_id)+'" alt="Illustration till sida '+(page+1)+'"><div class="page-text"><span class="eyebrow">'+esc(book.snapshot.child.name)+'s saga</span><p>'+esc(p.text)+'</p></div></div><nav class="row reader-nav" aria-label="Bläddra"><button class="quiet" data-action="prev" '+(page===0?'disabled':'')+' aria-label="Föregående sida">←</button><span>'+(page+1)+' / '+book.pages.length+'</span><button class="quiet" data-action="next" '+(page===book.pages.length-1?'disabled':'')+' aria-label="Nästa sida">→</button></nav></article>';
 let x;$('#spread').ontouchstart=e=>x=e.changedTouches[0].clientX;$('#spread').ontouchend=e=>{const d=e.changedTouches[0].clientX-x;if(Math.abs(d)>60)turn(d<0?1:-1);};
}
function turn(d){if(!book||book.status!=='ready'||!document.body.classList.contains('reading'))return;page=Math.max(0,Math.min(book.pages.length-1,page+d));renderReader();}
async function submit(form,fn){const b=form.querySelector('button[type=submit],button:not([type])');if(b)b.disabled=true;try{await fn();}catch(e){toast(e.message);}finally{if(b)b.disabled=false;}}
document.addEventListener('click',async e=>{
 const el=e.target.closest('button,[data-return-family]');if(!el)return;
 try{
 if(el.dataset.tab){tab=el.dataset.tab;await renderHome();return;}
 if(el.dataset.person){await showPerson(el.dataset.person);return;}
 if(el.dataset.returnFamily){page=0;await selectFamily(el.dataset.returnFamily);return;}
 if(el.dataset.removeRelation){await api('/relations/'+el.dataset.removeRelation,'DELETE');await showPerson(person.id);return;}
 if(el.dataset.editMemory){const m=family.memories.find(m=>m.id===el.dataset.editMemory);modal('<h2>Rätta en anteckning</h2><form id="edit-memory"><label>Datum<input name="event_date" type="date" value="'+esc(m.event_date)+'" required></label><label>Text<textarea name="text" maxlength="5000" required>'+esc(m.text)+'</textarea></label><details><summary>Ursprunglig text · '+date(m.created_at)+'</summary><p>'+esc(m.original_text)+'</p></details><p><button>Spara rättelse</button></p></form>');$('#edit-memory').onsubmit=async e=>{e.preventDefault();await submit(e.target,async()=>{await api('/memories/'+m.id,'PUT',Object.fromEntries(new FormData(e.target)));dialog.close();showPerson(person.id);});};return;}
 if(el.dataset.deleteMemory){if(confirm('Radera denna anteckning?')){await api('/memories/'+el.dataset.deleteMemory,'DELETE');await showPerson(person.id);}return;}
 switch(el.dataset.action){
 case 'new-family':modal('<h2>En familj att drömma med</h2><form id="family-form"><label>Familjens namn<input name="name" required maxlength="100" placeholder="Familjen…"></label><p class="muted">Familjen blir synlig och redigerbar för alla.</p><button>Skapa familj</button></form>');$('#family-form').onsubmit=async e=>{e.preventDefault();await submit(e.target,async()=>{await flush();const f=await api('/families','POST',Object.fromEntries(new FormData(e.target)));dialog.close();await selectFamily(f.id);});};break;
 case 'delete-family':if(confirm('Ta bort '+family.name+' och alla personer, foton och böcker i familjen? Det går inte att ångra.')){await flush();await api('/families/'+family.id,'DELETE');family=null;person=null;book=null;localStorage.removeItem('godnatt-family');await start();}break;
 case 'add-person':personForm();break;
 case 'edit-person':await flush();family=await api('/families/'+family.id);person=family.people.find(p=>p.id===person.id);personForm(person);break;
 case 'relation':relationForm();break;
 case 'new-book':await newBook();break;
 case 'home':await flush();await selectFamily(family.id);break;
 case 'finish-memory':await flush();await showPerson(person.id);break;
 case 'remove-photo':await api('/people/'+person.id+'/photo','DELETE');await showPerson(person.id);break;
 case 'delete-person':if(confirm('Ta bort '+person.name+' och personens livslinje? Sparade böcker finns kvar.')){await flush();await api('/people/'+person.id,'DELETE');await selectFamily(family.id);}break;
 case 'prev':turn(-1);break;
 case 'next':turn(1);break;
 case 'reload':await start();break;
 }
 }catch(e){toast(e.message);}
});
document.addEventListener('keydown',e=>{if(['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)||dialog.open)return;if(e.key==='Escape'&&document.body.classList.contains('reading')){selectFamily(book.family_id).catch(e=>toast(e.message));return;}if(e.key==='ArrowRight')turn(1);if(e.key==='ArrowLeft')turn(-1);});
$('#close-dialog').onclick=()=>dialog.close();
$('#help').onclick=()=>modal('<h2>Godnatt på hemskärmen</h2><p><strong>iPhone och iPad:</strong> öppna länken i Safari. Välj Dela och sedan Lägg till på hemskärmen.</p><p><strong>Android:</strong> välj Installera appen i webbläsarens meny.</p><p>Du kan också använda Godnatt direkt via länken. Internet behövs för sparade familjer och nya böcker.</p>');
window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();installPrompt=e;$('#install').hidden=false;});
$('#install').onclick=async()=>{if(installPrompt){await installPrompt.prompt();installPrompt=null;$('#install').hidden=true;}};
window.addEventListener('beforeunload',e=>{if(pending.size||saving){e.preventDefault();e.returnValue='';}});
window.addEventListener('online',()=>toast('Du är ansluten igen.'));
window.addEventListener('offline',()=>toast('Internet saknas. Anslut för att spara och öppna böcker.'));
if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});
start();
