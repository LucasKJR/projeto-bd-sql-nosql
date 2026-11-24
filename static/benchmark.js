'use strict';
(async()=>{
 const $=id=>document.getElementById(id),n=(tag,text)=>{const e=document.createElement(tag);e.textContent=text;return e;};
 const num=(v,precision)=>v.toLocaleString('pt-BR',{minimumFractionDigits:precision,maximumFractionDigits:precision});
 const time=v=>v>=1000?num(v/1000,2)+' s':num(v,2)+' ms';
 try{
  const r=await fetch('/api/benchmark-history',{cache:'no-store'});if(!r.ok)throw Error();
  const data=await r.json(),rows=data.rows;
  if(!Array.isArray(rows)||rows.length!==4||!rows.every(x=>Number.isFinite(x.postgres_ms)&&Number.isFinite(x.mongo_ms)))throw Error();
  const q4=rows.find(row=>row.code==='Q4');
  $('benchmark-date').textContent='Medido em '+data.run_date.split('-').reverse().join('/');
  $('highlight-pct').textContent=num(q4.lower_pct,0)+'%';
  $('highlight-detail').textContent=time(q4.postgres_ms)+' PostgreSQL × '+time(q4.mongo_ms)+' MongoDB · '+q4.samples+' amostras por banco';
  for(const result of rows){
   const tr=document.createElement('tr');if(result.code==='Q4')tr.className='q4';
   const query=n('td',result.code+' · '+result.label);
   query.append(n('small',result.scope+' · '+num(result.samples,0)+' amostras por banco'));
   const win=document.createElement('td');win.append(n('b',result.winner),n('small',num(result.lower_pct,1)+'% menor'));
   tr.append(query,n('td',time(result.postgres_ms)),n('td',time(result.mongo_ms)),win);$('benchmark-table').tBodies[0].append(tr);
  }
  $('benchmark-table').hidden=false;$('benchmark-status').textContent='';
 }catch(e){$('benchmark-status').className='error-note';$('benchmark-status').textContent='Não foi possível ler os resultados arquivados. Confira os arquivos em results/.';}
})();
