const fs=require('fs');
const html=fs.readFileSync(""+'/workspace/terminal-lineup/site/13f-tracker/index.html','utf8');
const data=JSON.parse(fs.readFileSync(""+'/workspace/terminal-lineup/site/13f-tracker/data.json','utf8'));
const els={};
function mk(id){return els[id]={id,textContent:'',innerHTML:'',className:''};}
['banner','meta','main','receipt'].forEach(mk);
global.document={getElementById:id=>els[id]};
global.fetch=()=>Promise.resolve({ok:true,json:()=>Promise.resolve(data)});
const script=html.match(/<script>([\s\S]*)<\/script>/)[1];
eval(script);
setTimeout(()=>{
  const t=els.main.innerHTML;
  const checks=[
    (t.match(/<section class="group">/g)||[]).length===20,
    t.includes('BlackRock, Inc.'), t.includes('Nvidia Corporation'),
    t.includes('1,941,918,386')||t.includes('1941918386')||t.includes('1,941,918,386'),
    t.includes('How it changed since'), els.meta.textContent.includes('June 30, 2026'),
    els.receipt.textContent.includes('8,857 holders'),
    t.includes('Wellington Management Group LLP')];
  console.log(checks); console.log('meta:',els.meta.textContent.slice(0,120));
  if(checks.includes(false)) process.exit(1);
  console.log('RENDER PASS');
},50);
