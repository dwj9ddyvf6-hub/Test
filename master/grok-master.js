/* GrokBot design shell behaviour for the Master edition (R2).
   Presentation only: adds the design bar and the C1 eyebrow grammar
   to the app's own cards/panels as they render. Reads no data. */
(function(){"use strict";
function ready(f){if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",f);else f();}
ready(function(){
  if(!document.querySelector(".gb-mbar")){var b=document.createElement("div");b.className="gb-mbar";b.innerHTML='<span class="gb-dot"></span><span>Master Terminal</span><a href="../">Combined terminal</a><a href="../terminal-lineup/site/">Engines and Tools</a>';document.body.insertBefore(b,document.body.firstChild);}
  function grammar(){Array.prototype.forEach.call(document.querySelectorAll(".card,.panel,.tile,.read,.view section"),function(c){if(c.querySelector(":scope > .gb-kicker"))return;var h=c.querySelector("h1,h2,h3");if(!h)return;var k=document.createElement("p");k.className="gb-kicker";k.textContent=(document.title||"Master").slice(0,60);c.insertBefore(k,c.firstChild);});}
  grammar();[1200,3000,6000].forEach(function(ms){setTimeout(grammar,ms);});
  new MutationObserver(function(){grammar();}).observe(document.body,{childList:true,subtree:true});
});
})();
