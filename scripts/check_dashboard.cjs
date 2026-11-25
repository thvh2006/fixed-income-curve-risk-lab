// DOM harness validates browser mathematics, control contracts and all views.
// Native browser rendering and mobile inspection are separate review steps.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const R=path.resolve(__dirname,'..'),D=JSON.parse(fs.readFileSync(path.join(R,'artifacts/release/research.json')));
class Element{constructor(id){this.id=id;this.html='';this.value=({settlement:'2025-12-31',maturity:'2030-12-31',coupon:'4',shock:'0',snapshot:String(D.history.length-1)})[id]||'';}set innerHTML(s){this.html=s}get innerHTML(){return this.html}focus(){}click(){}}
const es={},el=id=>es[id]??=new Element(id),document={querySelector:s=>el(s.replace(/^#/,'')),querySelectorAll:()=>[],createElement:()=>new Element('new')};
const ctx={location:{hostname:'localhost'},window:{RESEARCH:D,scrollTo:()=>{},location:{hash:'#bond-pricer'},history:{replaceState:(_,__,hash)=>{ctx.window.location.hash=hash}},addEventListener:()=>{}},document,console,Date,Blob,URL,fetch:async()=>({ok:true,json:async()=>({status:'pending'})})};vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(R,'dashboard/app.js'),'utf8'),ctx);
assert(es.pricer.innerHTML.includes(D.bond.dirty.toFixed(6)));assert.equal(ctx.window.location.hash,'#bond-pricer');
for(let i=0;i<8;i++){vm.runInContext(`active=${i};render()`,ctx);assert(es.content.innerHTML.length>200);assert(!es.content.innerHTML.includes('NaN'));}
for(const g of D.golden_cases){let got=vm.runInContext(`py(flows('2025-12-31','${2025+g.years}-12-31',${g.coupon}).cf,${g.yield_rate})`,ctx);assert(Math.abs(got-g.dirty)<1e-8);}
for(const g of D.curve_golden_cases){let got=vm.runInContext(`(()=>{let b=flows('${g.settlement}','${g.maturity}',${g.coupon});let p=price(b.cf,boot(D.history.at(-1).par),K.map(()=>${g.shock_bp/10000}));return {dirty:p,accrued:b.ai,ytm:solve(b.cf,p)}})()`,ctx);for(let k of ['dirty','accrued','ytm'])assert(Math.abs(got[k]-g[k])<1e-8,`${k}: ${got[k]} != ${g[k]}`);}
vm.runInContext('active=1;render()',ctx);assert(es.pricer.innerHTML.includes(D.bond.dirty.toFixed(6)));
for(const [cp,bp]of [[0,0],[6,100],[4,-100],[8,200]]){es.coupon.value=String(cp);es.shock.value=String(bp);vm.runInContext('computeBond()',ctx);assert(!es.pricer.innerHTML.includes('role="alert"'));let got=vm.runInContext(`price(flows('2025-12-31','2030-12-31',${cp/100}).cf,boot(D.history.at(-1).par),K.map(()=>${bp/10000}))`,ctx);assert(Number.isFinite(got));}
for(const id of ['settlement','maturity','coupon','shock']){let before=el(id).value;el(id).value='';vm.runInContext('computeBond()',ctx);assert(es.pricer.innerHTML.includes('Complete every bond input'));el(id).value=before;}
es.settlement.value='2031-01-01';vm.runInContext('computeBond()',ctx);assert(es.pricer.innerHTML.includes('Settlement must precede maturity'));
console.log(JSON.stringify({views:8,golden_yield_cases:D.golden_cases.length,curve_golden_cases:D.curve_golden_cases.length,curve_scenarios:4,blank_guards:4,invalid_date:true,native_browser:false}));
