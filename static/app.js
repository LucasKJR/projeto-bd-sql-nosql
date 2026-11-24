'use strict';
const $=id=>document.getElementById(id);
const money=cents=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(Number(cents)/100);
const timeFormatter=new Intl.NumberFormat('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
const ms=v=>Number.isFinite(v)?timeFormatter.format(v)+' ms':'—';
const names={postgres:'PostgreSQL',mongo:'MongoDB'};
let generation=0,controller,navGeneration=0,navController;
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
 $('order-context').textContent=`Pedido #${$('order_id').value} · ${names[source]}`;
 renderOrder(order.rows[0],order.error);
 const batch=results[source].batch;$('batch-summary').textContent=batch.error||batch.rows.length+' pedidos retornados';$('batch-links').replaceChildren();if(!batch.error)batch.rows.forEach(row=>{const b=node('button','#'+row.id);b.type='button';b.style.margin='3px';b.addEventListener('click',()=>navigateOrder(row.id));$('batch-links').append(b);}); $('batch').textContent=batch.error||(!batch.rows.length?'Lote não encontrado.':batch.rows.length+' pedidos retornados. Prévia de 3:\n'+JSON.stringify(batch.rows.slice(0,3),null,2));
 const labels=['Q1 · Pedido','Q2 · Vendas/dia','Q3 · Produtos','Q4 · Lote 100'];
 const rows=['order','daily','top','batch'].map((q,i)=>{
  const a=results.postgres[q],b=results.mongo[q],speed=Dashboard.comparisonResult(a.elapsed_ms,b.elapsed_ms);
  return [labels[i],a.error?'Erro':ms(a.elapsed_ms),b.error?'Erro':ms(b.elapsed_ms),speed?speed.winner:'—',speed?ms(speed.delta):'—'];
 });
 $('comparison').className='table-scroll';$('comparison').replaceChildren(table(['Consulta','PostgreSQL','MongoDB','Mais rápido','Diferença'],rows,'comparison-table'));
}
async function refresh(event){
 if(event)event.preventDefault();if(controller){controller.abort();return;}const token=++generation;let filters;
 try{filters=Dashboard.filters($('start').value,$('end').value,$('order_id').value);}catch(e){$('status').textContent=e.message;$('status').className='error';return;}
 if(navController)navController.abort();navGeneration++;controller=new AbortController();const signal=controller.signal,source=$('source').value;
 $('refresh').disabled=false;$('refresh').textContent='Cancelar consulta';$('status').className='';$('status').textContent='Iniciando consultas…';let timedOut=false;const deadline=setTimeout(()=>{timedOut=true;controller?.abort();},120000);
 $('order-readable').textContent='Carregando pedido…';for(const q of ['daily','top','order','batch']){$(q+'-time').textContent='— ms';message(q,'Carregando…');}
 for(const id of ['revenue','count','ticket'])$(id).textContent='—';message('comparison','Carregando…');$('comparison-context').textContent='';$('batch-summary').textContent='Carregando…';$('batch-links').replaceChildren();
 const results={postgres:{},mongo:{}};
 try{
  for(const q of ['order','daily','top','batch'])for(const s of ['postgres','mongo']){
   try{
    $('status').textContent=`Consultando ${names[s]} · ${q} (${Object.values(results).reduce((n,r)=>n+Object.keys(r).length,0)+1}/8)…`;
    const response=await fetch(Dashboard.queryURL(s,q,filters),{signal,cache:'no-store'});
    const payload=await response.json();if(!response.ok)throw Error(typeof payload.detail==='string'?payload.detail:payload.error||'Erro HTTP '+response.status);
    if(!Array.isArray(payload.rows)||!Number.isFinite(payload.elapsed_ms))throw Error('Resposta inválida da API.');
    results[s][q]=payload;
   }catch(error){if(error.name==='AbortError')throw error;results[s][q]={error:names[s]+': '+error.message,rows:[]};}
  }
  if(token!==generation)return;render(source,results);$('comparison-context').textContent=`${filters.start} a ${filters.end} · Pedido e início do lote #${filters.order_id}`;
  const errors=Object.values(results).flatMap(r=>Object.values(r)).filter(r=>r.error).length;
  $('status').className=errors?'error':'';$('status').textContent=errors?`${errors} consulta(s) falharam. Confira se os bancos estão ativos e a carga foi concluída. Indicadores exibidos: ${names[source]}.`:`Atualizado às ${new Date().toLocaleTimeString('pt-BR')} · Indicadores: ${names[source]}`;
 }catch(error){$('status').className='error';$('status').textContent=error.name==='AbortError'?(timedOut?'Consulta excedeu 120 segundos. Tente um período menor.':'Consulta cancelada. Ajuste os filtros e clique em Consultar bancos.'):error.message;for(const q of ['daily','top','order','batch'])message(q,'Consulta não concluída.');message('comparison','Consulta não concluída.');$('batch-summary').textContent='Consulta não concluída.';$('order-readable').textContent='Consulta não concluída.';}
 finally{clearTimeout(deadline);if(token===generation){controller=null;$('refresh').disabled=false;$('refresh').textContent='Consultar bancos';}}
}
$('filters').addEventListener('submit',refresh);
for(const id of ['source','start','end','order_id'])$(id).addEventListener('change',()=>{if(controller)controller.abort();else $('status').textContent='Filtros alterados. Consulte para atualizar.';});

async function navigateOrder(id){
 if(controller){$('status').textContent='Cancele ou aguarde a comparação antes de navegar.';return;}
 if(!Number.isSafeInteger(id)||id<1)return;
 if(navController)navController.abort();navController=new AbortController();const signal=navController.signal,token=++navGeneration,source=$('source').value;
 $('order_id').value=id;$('lookup-id').value=id;$('order-context').textContent=`Consultando pedido #${id} · ${names[source]}…`;$('order').textContent='Carregando pedido…';$('order-readable').textContent='Carregando pedido…';
 const timeout=setTimeout(()=>navController?.abort(),15000);
 try{const response=await fetch(Dashboard.queryURL(source,'order',{start:'2025-01-01',end:'2026-01-01',order_id:id}),{signal,cache:'no-store'});const data=await response.json();if(!response.ok)throw Error(data.error||'Falha ao consultar');if(token!==navGeneration)return;renderOrder(data.rows[0]);$('order-time').textContent=ms(data.elapsed_ms);$('order-context').textContent=`Pedido #${id} · ${names[source]}`;$('previous-order').disabled=id===1;
 }catch(e){if(token===navGeneration){$('order').textContent=e.name==='AbortError'?'Navegação cancelada ou excedeu 15s.':e.message;$('order-time').textContent='— ms';$('order-readable').textContent=$('order').textContent;}}
 finally{clearTimeout(timeout);if(token===navGeneration)navController=null;}
}
$('previous-order').addEventListener('click',()=>navigateOrder(Number($('order_id').value)-1));
$('next-order').addEventListener('click',()=>navigateOrder(Number($('order_id').value)+1));

function renderOrder(order,error){
 const target=$('order-readable');target.replaceChildren();
 if(error||!order){target.textContent=error||'Pedido não encontrado.';$('order').textContent=target.textContent;return;}
 $('lookup-id').value=order.id;
 target.append(node('h3',`Pedido #${order.id} · Cliente #${order.customer_id}`));
 target.append(node('p',`Status: ${order.status} · Data UTC: ${new Date(order.created_at).toLocaleString('pt-BR',{timeZone:'UTC'})}`));
 target.append(node('p',`Total: ${money(order.total_cents)} · ${order.items.length} linhas · ${order.items.reduce((n,i)=>n+i.quantity,0)} unidades`));
 const wrap=node('div');wrap.style.overflowX='auto';wrap.append(table(['Linha','Produto','Nome','Qtd.','Unitário','Subtotal'],Dashboard.itemRows(order.items).map(r=>[...r.slice(0,4),money(r[4]),money(r[5])])));target.append(wrap);
 $('order').textContent=JSON.stringify(order,null,2);
}
$('lookup-button').addEventListener('click',()=>{const id=Number($('lookup-id').value);if(!Number.isSafeInteger(id)||id<1){$('order-readable').textContent='Informe um ID inteiro positivo.';return;}navigateOrder(id);});
$('lookup-id').addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();$('lookup-button').click();}});
$('download-evidence').href=URL.createObjectURL(new Blob([$('load-evidence-json').textContent],{type:'application/json'}));
