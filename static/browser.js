(() => {
 const $=id=>document.getElementById(id), esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const money=v=>(v/100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
 let collection='orders', after=0, next=null, history=[], generation=0, controller;
 const table=(heads,rows)=>'<div style="overflow-x:auto"><table><thead><tr>'+heads.map(h=>'<th>'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(v=>'<td>'+esc(v)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
 function detail(doc){
  $('document-detail').innerHTML=doc ? '<h3>'+esc(collection)+' / #'+esc(doc._id)+'</h3>'+table(['Campo','Valor'],Object.entries(doc).filter(([k])=>k!=='items').map(([k,v])=>[k,k==='total_cents'?money(v)+' ('+v+' centavos)':v]))+(doc.items?'<h4>Itens incorporados ('+doc.items.length+')</h4>'+table(['Linha','Produto','Nome','Quantidade','Unitário','Subtotal'],doc.items.map(i=>[i.position+1,i.product_id,i.product_name,i.quantity,money(i.unit_cents),money(i.quantity*i.unit_cents)])):'') : '<p>Documento não encontrado.</p>';
  $('document-json').textContent=doc?JSON.stringify(doc,null,2):'Nenhum documento.';
 }
 async function request(id){
  controller?.abort();controller=new AbortController();const mine=++generation;
  $('collection-status').textContent='Consultando MongoDB…';
  const activeController=controller;
  const timer=setTimeout(()=>activeController.abort(),15000);
  try{
   const qs=new URLSearchParams({collection});qs.set(id===undefined?'after':'id',id===undefined?after:id);
   const res=await fetch('/api/documents?'+qs,{signal:controller.signal});const data=await res.json();if(!res.ok)throw Error(data.error||'Consulta falhou');if(mine!==generation)return;
   if(id!==undefined){detail(data.document);$('collection-status').textContent=data.document?'Documento #'+id+' consultado no MongoDB.':'Documento não encontrado.';}
   else{
    next=data.next_after;$('collection-prev').disabled=!history.length;$('collection-next').disabled=next===null;
    $('collection-list').replaceChildren();
    data.documents.forEach(doc=>{const b=document.createElement('button');b.type='button';b.style.cssText='text-align:left;display:block;width:100%;margin:6px 0';b.textContent='#'+doc._id+' · '+(doc.name||'Cliente '+doc.customer_id+' · '+doc.status+' · '+money(doc.total_cents));b.onclick=()=>{$('document-id').value=doc._id;request(doc._id);};$('collection-list').append(b);});
    detail(null);$('document-detail').textContent='Clique em um documento para ver seus campos e itens.';$('collection-status').textContent=data.documents.length+' documentos · '+collection+' · IDs '+(data.documents.length?data.documents[0]._id+' a '+data.documents.at(-1)._id:'sem resultados')+' · consulta real';
   }
  }catch(e){if(mine===generation)$('collection-status').textContent=e.name==='AbortError'?'Consulta interrompida ou tempo excedido. Tente novamente.':e.message;}
  finally{clearTimeout(timer);}
 }
 document.querySelectorAll('[data-collection]').forEach(b=>b.onclick=()=>{collection=b.dataset.collection;after=0;history=[];next=null;document.querySelectorAll('[data-collection]').forEach(t=>t.setAttribute('aria-pressed',String(t===b)));request();});
 $('collection-next').onclick=()=>{if(next!==null){history.push(after);after=next;request();}};
 $('collection-prev').onclick=()=>{if(history.length){after=history.pop();request();}};
 $('collection-reload').onclick=()=>request();
 $('document-search').onsubmit=e=>{e.preventDefault();const id=$('document-id').value;if(!/^\d+$/.test(id)||Number(id)<1||Number(id)>2147483647){$('collection-status').textContent='Informe um ID inteiro positivo válido.';return;}request(id);};
})();
