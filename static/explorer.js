'use strict';
(() => {
 const $=id=>document.getElementById(id),n=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
 const order={customer_id:'int',created_at:'date',status:'status',total_cents:'int'};
 const item={position:'int',product_id:'int',product_name:'text',quantity:'int',unit_cents:'int'};
 const catalog={
  postgres:{orders:{id:'int',...order},items:{order_id:'int',...item},customers:{id:'int',name:'text'},products:{id:'int',sku:'text',name:'text'}},
  mongo:{orders:{_id:'int',...order,items:'object',...Object.fromEntries(Object.entries(item).map(([k,v])=>['items.'+k,v]))},customers:{_id:'int',name:'text'},products:{_id:'int',sku:'text',name:'text'}}
 };
 const label={orders:'Pedidos',items:'Itens do pedido',customers:'Clientes',products:'Produtos'};
 const types={int:['eq','gte','lte','lt','gt'],date:['gte','lt'],status:['eq'],text:['eq','prefix']};
 const operators={eq:'É igual a',gte:'Maior ou igual',lte:'Menor ou igual',lt:'Menor que',gt:'Maior que',prefix:'Começa com'};
 let source=new URLSearchParams(location.search).get('source')==='mongo'?'mongo':'postgres',entity='orders',filters=[],selected=[],limit=20,pages=[],after=null,next=null,seq=0,ctrl=null,dirty=true;
 function options(el,entries){el.replaceChildren(...entries.map(([v,t])=>new Option(t,v)));}
 function schema(){return catalog[source][entity];}
 function pageButtons(){ $('page-number').textContent='Página '+(pages.length+1);$('page-prev').disabled=dirty||pages.length===0;$('page-next').disabled=dirty||next===null; }
 function markDirty(){
  seq++;ctrl?.abort();ctrl=null;dirty=true;next=null;pages=[];after=null;pageButtons();
  $('explorer-status').className='';$('explorer-status').textContent='';$('query-time').hidden=true;
  $('result-view').replaceChildren(n('div','Execute a consulta para ver o resultado.'));$('result-view').firstChild.className='empty-result';
 }
 function addFilter(){
  if($('conditions').children.length>=3)return;
  const row=n('div');row.className='condition';
  const select=entries=>{const e=n('select');options(e,entries);return e;},wrap=(title,el)=>{const e=n('label',title);e.append(el);return e;};
  const f=select([['','Selecione'],...Object.entries(schema()).filter(([,type])=>type!=='object').map(([k])=>[k,k])]);
  const op=select([]), slot=n('label'),remove=n('button','×');
  remove.className='subtle';remove.type='button';remove.setAttribute('aria-label','Remover filtro');
  remove.onclick=()=>{row.remove();if(!$('conditions').children.length)addFilter();$('add-filter').disabled=false;markDirty();};
  function setField(){
   const kind=schema()[f.value];
   options(op,(types[kind]||['']).map(k=>[k,k?(kind==='date'?(k==='gte'?'A partir de (UTC)':'Antes de (UTC)'):operators[k]):'Selecione']));
   op.disabled=!kind;
   let value;
   if(kind==='status')value=select([['concluido','Concluído'],['criado','Criado'],['cancelado','Cancelado']]);
   else{value=n('input');value.type=kind==='date'?'date':kind==='int'?'number':'text';value.required=!!kind;if(kind==='int'){value.min=0;value.max=9999999999999;}if(kind==='text')value.maxLength=80;}
   value.disabled=!kind;value.className='filter-value';value.oninput=markDirty;
   slot.replaceChildren(document.createTextNode('Valor'),value);
  }
  f.className='filter-field';op.className='filter-op';f.onchange=()=>{setField();markDirty();};op.onchange=markDirty;setField();
  row.append(wrap('Campo',f),wrap('Operador',op),slot,remove);$('conditions').append(row);
  $('add-filter').disabled=$('conditions').children.length>=3;
 }
 function makeTable(columns,rows){
  const table=n('table'), head=n('thead'), header=n('tr'), body=n('tbody');
  columns.forEach(c=>{const th=n('th',c);th.scope='col';header.append(th);});head.append(header);table.append(head,body);
  rows.forEach(r=>{const tr=n('tr');columns.forEach(c=>tr.append(n('td',String(r[c]??'—'))));body.append(tr);});
  return table;
 }
 function view(data){
  const target=$('result-view');target.replaceChildren();
  if(!data.rows.length){const empty=n('div','Nenhum resultado para os filtros escolhidos.');empty.className='empty-result';target.append(empty);return;}
  if(data.source==='postgres'){target.append(makeTable(data.columns,data.rows));return;}
  data.rows.forEach((row,i)=>{
   const d=n('details'), tag=[row._id===undefined?null:'#'+row._id,row.name,row.status].filter(Boolean).join(' · ')||'Documento '+(i+1);
   const fields=n('dl');d.className='doc-result';fields.className='doc-fields';d.append(n('summary',tag));
   for(const [key,value] of Object.entries(row))if(!Array.isArray(value))fields.append(n('dt',key),n('dd',String(value??'—')));
   if(fields.childNodes.length)d.append(fields);
   for(const [key,array] of Object.entries(row))if(Array.isArray(array)){
    const group=n('details'), wrap=n('div');wrap.className='subtable';
    group.append(n('summary',key+' · '+array.length+' itens'),wrap);
    if(array.length)wrap.append(makeTable(Object.keys(array[0]),array));
    d.append(group);
   }
   target.append(d);
  });
 }
 async function run(){
  ctrl?.abort();const token=++seq,active=new AbortController();ctrl=active;dirty=false;
  next=null;$('page-prev').disabled=$('page-next').disabled=true;
  $('explorer-status').className='';$('explorer-status').textContent='Consultando…';$('query-time').hidden=true;$('result-view').replaceChildren();
  const query=new URLSearchParams({source,entity,filters:JSON.stringify(filters),select:JSON.stringify(selected),limit:String(limit)});
  if(after)query.set('after',JSON.stringify(after));
  const timeout=setTimeout(()=>active.abort(),15000);
  try{
   const r=await fetch('/api/explore?'+query,{signal:active.signal,cache:'no-store'}),d=await r.json();
   if(token!==seq)return;if(!r.ok)throw Error(d.error||'Falha na consulta.');
   view(d);next=d.next;$('explorer-status').textContent=d.rows.length+' '+(source==='mongo'?'documentos':'linhas')+' nesta página';
   $('query-time').hidden=false;$('query-time').textContent=d.elapsed_ms.toLocaleString('pt-BR')+' ms';
  }catch(e){if(token===seq){$('explorer-status').className='error-note';$('explorer-status').textContent=e.name==='AbortError'?'Tempo limite. Tente filtros mais específicos.':e.message;}}
  finally{clearTimeout(timeout);if(token===seq){ctrl=null;pageButtons();}}
 }
 function resetFilters(){$('conditions').replaceChildren();addFilter();markDirty();}
 function selectEntity(name){
  entity=name;
  for(const b of $('entity-list').querySelectorAll('button'))b.setAttribute('aria-pressed',String(b.dataset.entity===entity));
  $('entity-title').textContent=(source==='postgres'?'public.':'bd_lab.')+entity;
  $('entity-type').textContent=(source==='postgres'?'Tabela':'Coleção')+' · '+label[entity];
  $('select-fields').replaceChildren(...Object.keys(schema()).filter(k=>!k.includes('.')).map(k=>{
   const chip=n('label'), box=n('input');box.type='checkbox';box.checked=k!=='items';box.value=k;box.onchange=markDirty;chip.className='field-chip';chip.append(box,n('span',k));return chip;
  }));
  resetFilters();
 }
 function choose(name){
  source=name;const u=new URL(location.href);u.searchParams.set('source',source);history.replaceState(null,'',u);
  document.querySelectorAll('[data-engine]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.engine===source)));
  $('schema-title').textContent=source==='postgres'?'Tabelas':'Coleções';
  $('result-title').textContent=source==='postgres'?'Linhas da tabela':'Documentos da coleção';
  $('entity-list').replaceChildren(...Object.keys(catalog[source]).map(k=>{const b=n('button');b.type='button';b.append(n('span',label[k]),n('small',k));b.dataset.entity=k;b.onclick=()=>selectEntity(k);return b;}));
  selectEntity('orders');
 }
 $('add-filter').onclick=()=>{addFilter();markDirty();};$('clear-filter').onclick=resetFilters;
 $('page-limit').onchange=markDirty;
 $('select-all').onclick=()=>{for(const box of $('select-fields').querySelectorAll('input'))box.checked=true;markDirty();};
 $('explorer-filter').onsubmit=e=>{
  e.preventDefault();
  filters=[...$('conditions').children].map(row=>['field','op','value'].map(name=>row.querySelector('.filter-'+name).value)).filter(([field])=>field);
  selected=[...$('select-fields').querySelectorAll('input:checked')].map(el=>el.value);
  if(!selected.length){$('explorer-status').className='error-note';$('explorer-status').textContent='Marque pelo menos um campo para ver o resultado.';return;}
  limit=Number($('page-limit').value);after=null;pages=[];run();
 };
 $('page-next').onclick=()=>{if(next!==null&&!dirty){pages.push(after);after=next;run();}};
 $('page-prev').onclick=()=>{if(pages.length&&!dirty){after=pages.pop();run();}};
 document.querySelectorAll('[data-engine]').forEach(b=>b.onclick=()=>choose(b.dataset.engine));
 choose(source);
})();
