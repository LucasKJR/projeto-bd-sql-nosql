const test=require('node:test'),assert=require('node:assert/strict');
const {toQuery,compareRows}=require('./compare-logic.js');
test('normalizes keys and time zone and compares by business ID regardless of order',()=>{
 const p=[{id:2,created_at:'2025-01-01T03:00:00Z'},{id:1,created_at:'2025-02-01T03:00:00Z'}];
 const m=[{_id:1,created_at:'2025-02-01T00:00:00-03:00'},{_id:2,created_at:'2025-01-01T00:00:00-03:00'}];
 assert.deepEqual(compareRows('orders',['created_at'],p,m).differences,[]);
});
test('same count or same selected values cannot hide a different business ID or typed data',()=>{
 assert.equal(compareRows('orders',['status'],[{id:1,status:'criado'}],[{_id:2,status:'criado'}]).differences.length,2);
 assert.equal(compareRows('orders',['total_cents'],[{id:1,total_cents:1030}],[{_id:1,total_cents:'1030'}]).differences.length,1);
});
test('translates Mongo ID field and fetches an internal parity key even if it is not selected',()=>{
 const q=new URL(toQuery('mongo','orders',[['id','gt','7']],['status'],10,[8]),'http://localhost').searchParams;
 assert.deepEqual(JSON.parse(q.get('select')),['_id','status']);
 assert.deepEqual(JSON.parse(q.get('filters')),[['_id','gt','7']]);
 assert.deepEqual(JSON.parse(q.get('after')),[8]);
});
