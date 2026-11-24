'use strict';
(() => {
 const $=id=>document.getElementById(id), node=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
 const ops={int:[['eq','É igual a'],['gte','Maior ou igual'],['lte','Menor ou igual'],['lt','Menor que'],['gt','Maior que']],date:[['gte','A partir de (UTC)'],['lt','Antes de (UTC)']],status:[['eq','É igual a']],text:[['eq','É igual a'],['prefix','Começa com']]};
 const names={postgres:'PostgreSQL',mongo:'MongoDB'};
 const ms=v=>v.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+' ms';
 let seq=0,ctrl=null,committed=null,next=null,after=null,pages=[],dirty=true;
 const entity=()=>$('compare-entity').value, schema=()=>CompareLab.catalog[entity()];
 const options=(el,entries)=>el.replaceChildren(...entries.map(([value,text])=>new Option(text,value)));
 function setStatus(text,error){$('compare-status').textContent=text;$('compare-status').className=error?'error-note':'';}
 function clear(){
  for(const id of ['pg-time','mongo-time','compare-winner'])$(id).textContent='—';
  $('compare-delta').textContent='';$('compare-agreement').textContent='';$('compare-agreement').className='agreement';
  $('compare-differences').hidden=true;$('compare-differences').replaceChildren();
  $('pg-rows').replaceChildren();$('mongo-rows').replaceChildren();
 }
 function buttons(){
  $('compare-page').textContent='Página '+(pages.length+1);
  $('compare-prev').disabled=dirty||!!ctrl||pages.length===0;
  $('compare-next').disabled=dirty||!!ctrl||next===null;
 }
 function draft(){
  seq++;ctrl?.abort();ctrl=null;committed=null;after=null;next=null;pages=[];dirty=true;
  clear();buttons();setStatus('Escolha os campos e clique em Comparar bancos.');
 }
 function add(){
  if($('conditions').childElementCount>=3)return;
  const row=node('div');row.className='condition';
  const wrap=(t,el)=>{const label=node('label',t);label.append(el);return label;};
  const field=node('select'),op=node('select'),vLabel=node('label'),remove=node('button','×');
  field.className='compare-field';op.className='compare-operator';
  options(field,[['','Selecione'],...Object.keys(schema()).map(k=>[k,k])]);
  function update(){
   const type=schema()[field.value];
   options(op,ops[type]||[['','Selecione']]);op.disabled=!type;
   const value=node(type==='status'?'select':'input');
   if(type==='status')options(value,[['concluido','Concluído'],['criado','Criado'],['cancelado','Cancelado']]);
   else{
    value.type=type==='date'?'date':type==='int'?'number':'text';value.required=!!type;
    if(type==='int'){value.min=0;value.max=9999999999999;}
    if(type==='text')value.maxLength=80;
   }
   value.disabled=!type;value.className='compare-value';value.oninput=draft;
   vLabel.replaceChildren(document.createTextNode('Valor'),value);
  }
  field.onchange=()=>{update();draft();};op.onchange=draft;
  remove.className='subtle';remove.type='button';remove.setAttribute('aria-label','Remover filtro');
  remove.onclick=()=>{row.remove();if(!$('conditions').childElementCount)add();$('compare-add').disabled=false;draft();};
  row.append(wrap('Campo',field),wrap('Operador',op),vLabel,remove);$('conditions').append(row);
  update();$('compare-add').disabled=$('conditions').childElementCount>=3;
 }
 function resetFilters(){$('conditions').replaceChildren();add();draft();}
 function setup(){
  $('select-fields').replaceChildren(...Object.keys(schema()).map(k=>{
   const label=node('label'),box=node('input');box.type='checkbox';box.value=k;box.checked=true;box.onchange=draft;
   label.className='field-chip';label.append(box,node('span',k));return label;
  }));
  resetFilters();
 }
 function render(source,target,rows,fields){
  if(!rows.length){const div=node('div','Nenhum registro.');div.className='empty-result';target.append(div);return;}
  if(source==='postgres'){
   const table=node('table'),head=node('thead'),tr=node('tr'),body=node('tbody');
   fields.forEach(k=>{const th=node('th',k);th.scope='col';tr.append(th);});head.append(tr);table.append(head,body);
   rows.forEach(r=>{const tr=node('tr');fields.forEach(k=>tr.append(node('td',String(r[k]??'—'))));body.append(tr);});target.append(table);
  }else{
   rows.forEach((r,i)=>{
    const d=node('details'),dl=node('dl');
    d.className='doc-result';dl.className='doc-fields';
    d.append(node('summary',fields.includes('id')?'Documento #'+r._id:'Documento '+(i+1)),dl);
    fields.forEach(k=>{const name=CompareLab.field(source,k);dl.append(node('dt',name),node('dd',String(r[name]??'—')));});
    target.append(d);
   });
  }
 }
 async function execute(){
  if(!committed)return;
  ctrl?.abort();const ticket=++seq,active=new AbortController();ctrl=active;dirty=false;next=null;
  const cfg=committed,cursor=after;clear();buttons();
  const timer=setTimeout(()=>active.abort(),26000);let current='';
  try{
   const result={};
   for(const source of ['postgres','mongo']){
    current=names[source];setStatus('Consultando '+current+'…');
    const r=await fetch(CompareLab.toQuery(source,cfg.entity,cfg.filters,cfg.fields,cfg.limit,cursor),{signal:active.signal,cache:'no-store'});
    const payload=await r.json();if(ticket!==seq)return;
    if(!r.ok)throw Error(payload.error||'Consulta não concluída.');
    if(payload.source!==source||!Array.isArray(payload.rows)||!Number.isFinite(payload.elapsed_ms))throw Error('Resposta inválida.');
    result[source]=payload;$(source==='postgres'?'pg-time':'mongo-time').textContent=ms(payload.elapsed_ms);
    render(source,$(source==='postgres'?'pg-rows':'mongo-rows'),payload.rows,cfg.fields);
   }
   const {postgres:pg,mongo}=result;
   const {differences}=CompareLab.compareRows(cfg.entity,cfg.fields,pg.rows,mongo.rows);
   const equivalent=differences.length===0 && JSON.stringify(pg.next)===JSON.stringify(mongo.next);
   const ag=$('compare-agreement');
   ag.classList.add(equivalent?'equal':'different');
   ag.textContent=equivalent?(pg.rows.length?'Os '+pg.rows.length+' registros e os campos selecionados batem nesta página.':'Nenhum registro nos dois bancos.'):'Os resultados desta página não batem.';
   setStatus(pg.rows.length+' linhas PostgreSQL · '+mongo.rows.length+' documentos MongoDB');
   if(equivalent&&pg.rows.length){
    const a=Number(pg.elapsed_ms.toFixed(2)),b=Number(mongo.elapsed_ms.toFixed(2));
    $('compare-winner').textContent=a===b?'Empate':a<b?'PostgreSQL':'MongoDB';
    $('compare-delta').textContent=ms(Math.abs(a-b))+' de diferença';
   }
   if(!equivalent){
    $('compare-delta').textContent='Sem vencedor: resultados diferentes.';
    $('compare-differences').hidden=false;
    if(differences.length)$('compare-differences').replaceChildren(...differences.slice(0,8).map(d=>node('li',d.missing?'ID '+d.id+' não retornado por '+d.missing:'ID '+d.id+': '+d.fields.join(', '))));
    else $('compare-differences').append(node('li','Os limites da página diferem entre os bancos.'));
   }
   next=equivalent?pg.next:null;
  }catch(error){
   if(ticket===seq)setStatus(current+': '+(error.name==='AbortError'?'tempo limite atingido.':error.message),true);
  }finally{clearTimeout(timer);if(ticket===seq){ctrl=null;buttons();}}
 }
 $('compare-form').onsubmit=e=>{
  e.preventDefault();
  const filters=[...$('conditions').children].map(row=>['field','operator','value'].map(k=>row.querySelector('.compare-'+k).value)).filter(([name])=>name);
  const fields=[...$('select-fields').querySelectorAll('input:checked')].map(el=>el.value);
  if(!fields.length){setStatus('Marque pelo menos um campo para comparar.',true);return;}
  committed={entity:entity(),limit:Number($('compare-limit').value),fields,filters};after=null;pages=[];execute();
 };
 $('compare-prev').onclick=()=>{if(!dirty&&pages.length){after=pages.pop();execute();}};
 $('compare-next').onclick=()=>{if(!dirty&&next){pages.push(after);after=next;execute();}};
 $('compare-entity').onchange=setup;$('compare-limit').onchange=draft;
 $('compare-add').onclick=()=>{add();draft();};$('compare-clear').onclick=resetFilters;
 $('compare-all').onclick=()=>{for(const check of $('select-fields').querySelectorAll('input'))check.checked=true;draft();};
 setup();
})();
