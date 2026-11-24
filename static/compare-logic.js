(function(root){
 const catalog={
  orders:{id:'int',customer_id:'int',created_at:'date',status:'status',total_cents:'int'},
  customers:{id:'int',name:'text'},
  products:{id:'int',sku:'text',name:'text'},
 };
 function field(source,k){return source==='mongo'&&k==='id'?'_id':k;}
 function toQuery(source,entity,filters,fields,limit,after){
  const q=new URLSearchParams({source,entity,filters:JSON.stringify(filters.map(([k,op,v])=>[field(source,k),op,v])),select:JSON.stringify([...new Set(['id',...fields])].map(k=>field(source,k))),limit:String(limit)});
  if(after)q.set('after',JSON.stringify(after));
  return '/api/explore?'+q;
 }
 function normalized(value,type){
  if(type!=='date'||typeof value!=='string')return value;
  const n=Date.parse(value);return Number.isFinite(n)?n:value;
 }
 function compareRows(entity,fields,pg,mongo){
  const map=(rows,key)=>new Map(rows.map(row=>[row[key],row]));
  const a=map(pg,'id'),b=map(mongo,'_id'),differences=[];
  if(a.size!==pg.length||b.size!==mongo.length||[...a.keys(),...b.keys()].some(id=>!Number.isSafeInteger(id)))throw Error('A resposta contém identificadores inválidos.');
  for(const id of new Set([...a.keys(),...b.keys()])){
   if(!a.has(id)||!b.has(id)){differences.push({id,fields:[],missing:a.has(id)?'MongoDB':'PostgreSQL'});continue;}
   const changed=fields.filter(k=>!Object.hasOwn(a.get(id),k)||!Object.hasOwn(b.get(id),field('mongo',k))||
      !Object.is(normalized(a.get(id)[k],catalog[entity][k]),normalized(b.get(id)[field('mongo',k)],catalog[entity][k])));
   if(changed.length)differences.push({id,fields:changed});
  }
  return {differences};
 }
 const api={catalog,field,toQuery,compareRows};if(typeof module!=='undefined')module.exports=api;else root.CompareLab=api;
})(typeof window==='undefined'?globalThis:window);
