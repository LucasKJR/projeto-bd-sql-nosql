const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {comparisonResult}=require('./logic.js');
test('filters, KPIs and timings lead; raw data and collection evidence remain accessible',()=>{
 const html=fs.readFileSync('static/index.html','utf8');
 const id=(name)=>html.indexOf('id="'+name+'"');
 assert.ok(id('filters')<id('revenue')&&id('revenue')<id('comparison')&&id('comparison')<id('collection-browser')&&id('collection-browser')<id('load-evidence'));
 assert.match(html, /Q4 no benchmark/);
 assert.match(html, /<details[^>]*>\s*<summary>IDs e JSON do lote/);
 assert.ok(id('load-evidence-json')>id('load-evidence'));
});
test('run ranking reports a measured winner/delta, display-precision tie, or no winner from incomplete data',()=>{
 assert.deepEqual(comparisonResult(10.12,5.88),{winner:'MongoDB',delta:4.24});
 assert.deepEqual(comparisonResult(1.12,2.35),{winner:'PostgreSQL',delta:1.23});
 assert.deepEqual(comparisonResult(1.1251,1.1252),{winner:'Empate',delta:0});
 assert.equal(comparisonResult(undefined,5.88),null);
});
