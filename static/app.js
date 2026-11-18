'use strict';
const $=id=>document.getElementById(id);
const money=cents=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(Number(cents)/100);
const ms=v=>Number.isFinite(v)?v.toFixed(2)+' ms':'—';
const names={postgres:'PostgreSQL',mongo:'MongoDB'};
let generation=0,controller;
function node(tag,text,className){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(className)n.className=className;return n;}
function message(id,text,error=false){const el=$(id);el.replaceChildren(node('p',text,error?'error-note':'empty'));}
function table(headers,rows,cls=''){const t=node('table',undefined,cls),thead=node('thead'),h=node('tr');headers.forEach(v=>h.append(node('th',v)));thead.append(h);t.append(thead);const body=node('tbody');rows.forEach(values=>{const tr=node('tr');values.forEach(v=>tr.append(node('td',v)));body.append(tr);});t.append(body);return t;}
function render(source,results){
 const daily=results[source].daily,top=results[source].top,order=results[source].order;
 for(const q of ['daily','top','order','batch'])$(q+'-time').textContent=ms(results[source][q]?.elapsed_ms);
 for(const id of ['revenue','count','ticket'])$(id).textContent='—';
 if(daily.error)message('daily',daily.error,true);else{
   const sum=Dashboard.summary(daily.rows);$('revenue').textContent=money(sum.total_cents);$('count').textContent=sum.orders.toLocaleString('pt-BR');$('ticket').textContent=sum.orders?money(sum.total_cents/sum.orders):'—';
   if(!daily.rows.length)message('daily','Nenhum pedido concluído nesse período.');else{$('daily').className='data-area';$('daily').replaceChildren(table(['Dia (UTC)','Pedidos','Receita'],daily.rows.map(r=>[r.day,Number(r.orders).toLocaleString('pt-BR'),money(r.total_cents)])));}
 }
 if(top.error)message('top',top.error,true);else if(!top.rows.length)message('top','Nenhum produto vendido nesse período.');else{
   $('top').className='data-area';$('top').replaceChildren();const max=Math.max(...top.rows.map(r=>Number(r.quantity)),1);
   top.rows.forEach(r=>{const row=node('div',undefined,'bar-row'),label=node('span','#'+r.product_id),track=node('div',undefined,'bar-track'),bar=node('div',undefined,'bar');bar.style.width=Math.max(0,Number(r.quantity)/max*100)+'%';track.append(bar);const value=node('span',Number(r.quantity).toLocaleString('pt-BR')+' un.');value.append(node('small',money(r.total_cents)));row.append(label,track,value);$('top').append(row);});
 }
 $('order').textContent=order.error||(!order.rows.length?'Pedido não encontrado.':JSON.stringify(order.rows[0],null,2));
 const batch=results[source].batch; $('batch').textContent=batch.error||(!batch.rows.length?'Lote não encontrado.':batch.rows.length+' pedidos retornados. Prévia de 3:\n'+JSON.stringify(batch.rows.slice(0,3),null,2));
 $('comparison').className='';$('comparison').replaceChildren(table(['Consulta','PostgreSQL','MongoDB'],['order','daily','top','batch'].map((q,i)=>[['Q1 · Pedido','Q2 · Vendas/dia','Q3 · Top produtos','Q4 · Lote 100'][i],results.postgres[q].error?'Erro':ms(results.postgres[q].elapsed_ms),results.mongo[q].error?'Erro':ms(results.mongo[q].elapsed_ms)]),'comparison-table'));
}
async function refresh(event){
 if(event)event.preventDefault();const token=++generation;if(controller)controller.abort();$('refresh').disabled=false;let filters;
 try{filters=Dashboard.filters($('start').value,$('end').value,$('order_id').value);}catch(e){$('status').textContent=e.message;$('status').className='error';return;}
 controller=new AbortController();const signal=controller.signal,source=$('source').value;
 $('refresh').disabled=true;$('status').className='';$('status').textContent='Consultando os dois bancos… Aguarde as oito consultas sequenciais.';
 for(const q of ['daily','top','order','batch']){$(q+'-time').textContent='— ms';message(q,'Carregando…');}
 for(const id of ['revenue','count','ticket'])$(id).textContent='—';message('comparison','Carregando…');
 const results={postgres:{},mongo:{}};
 try{
  for(const q of ['order','daily','top','batch'])for(const s of ['postgres','mongo']){
   try{
    const response=await fetch(Dashboard.queryURL(s,q,filters),{signal,cache:'no-store'});
    const payload=await response.json();if(!response.ok)throw Error(typeof payload.detail==='string'?payload.detail:payload.error||'Erro HTTP '+response.status);
    if(!Array.isArray(payload.rows)||!Number.isFinite(payload.elapsed_ms))throw Error('Resposta inválida da API.');
    results[s][q]=payload;
   }catch(error){if(error.name==='AbortError')throw error;results[s][q]={error:names[s]+': '+error.message,rows:[]};}
  }
  if(token!==generation)return;render(source,results);
  const errors=Object.values(results).flatMap(r=>Object.values(r)).filter(r=>r.error).length;
  $('status').className=errors?'error':'';$('status').textContent=errors?`${errors} consulta(s) falharam. Confira se os bancos estão ativos e a carga foi concluída. Indicadores exibidos: ${names[source]}.`:`Atualizado às ${new Date().toLocaleTimeString('pt-BR')} · Indicadores: ${names[source]} · Período: ${filters.start} até ${filters.end} (fim excluído).`;
 }catch(error){if(error.name!=='AbortError'){$('status').className='error';$('status').textContent=error.message;}}
 finally{if(token===generation)$('refresh').disabled=false;}
}
$('filters').addEventListener('submit',refresh);
for(const id of ['source','start','end','order_id'])$(id).addEventListener('change',refresh);
