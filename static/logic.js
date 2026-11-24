(function(root){
  function filters(start,end,id){
    if(!/^\d{4}-\d{2}-\d{2}$/.test(start)||!/^\d{4}-\d{2}-\d{2}$/.test(end)||!Number.isFinite(Date.parse(start))||!Number.isFinite(Date.parse(end))||start>=end)throw Error('Escolha um período válido: início anterior ao fim.');
    const order_id=Number(id);if(!Number.isSafeInteger(order_id)||order_id<1)throw Error('Informe um ID de pedido inteiro e positivo.');
    return {start,end,order_id};
  }
  function summary(rows){return rows.reduce((s,r)=>({orders:s.orders+Number(r.orders),total_cents:s.total_cents+Number(r.total_cents)}),{orders:0,total_cents:0});}
  function queryURL(source,query,f){return '/api/query?'+new URLSearchParams({source,query,...f});}
  function itemRows(items){return items.map(i=>[i.position+1,i.product_id,i.product_name,i.quantity,i.unit_cents,i.quantity*i.unit_cents]);}
  function comparisonResult(pg,mongo){
    if(!Number.isFinite(pg)||!Number.isFinite(mongo)||pg<0||mongo<0)return null;
    const a=Math.round(Number(pg.toFixed(2))*100),b=Math.round(Number(mongo.toFixed(2))*100);
    return {winner:a===b?'Empate':a<b?'PostgreSQL':'MongoDB',delta:Math.abs(a-b)/100};
  }
  const api={filters,summary,queryURL,itemRows,comparisonResult};if(typeof module!=='undefined')module.exports=api;else root.Dashboard=api;
})(typeof window!=='undefined'?window:globalThis);
