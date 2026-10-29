import * as evidenceContract from './evidence-contract.mjs?v=a888f2901385c4ce';
import * as researchAdapters from './research-adapters.mjs?v=f481f6e52e4ab537';
import * as marketOverview from './market-overview.mjs?v=ba16f82f6d3fb8ff';
import * as convergenceEngine from './convergence-engine.mjs?v=f9626ab00536dfe6';

window.SiliconEvidenceContract = evidenceContract;
window.SiliconResearchAdapters = researchAdapters;
window.SiliconMarketOverview = marketOverview;
window.SiliconConvergenceEngine = convergenceEngine;

const appScript = document.createElement('script');
appScript.src = new URL('./app.js?v=dcf81005b84f10db', import.meta.url).href;
appScript.onerror = () => {
  const app = document.getElementById('app');
  if (app) app.innerHTML = '<div class="boot-screen"><span class="brand-mark">S</span><span>Silicon Terminal could not load its local application script.</span></div>';
};
document.head.append(appScript);
