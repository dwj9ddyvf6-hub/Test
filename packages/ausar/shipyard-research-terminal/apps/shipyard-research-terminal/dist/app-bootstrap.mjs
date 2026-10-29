import * as evidenceContract from './evidence-contract.mjs';
import * as researchAdapters from './research-adapters.mjs';
import * as marketOverview from './market-overview.mjs';
import * as convergenceEngine from './convergence-engine.mjs';

window.SiliconEvidenceContract = evidenceContract;
window.SiliconResearchAdapters = researchAdapters;
window.SiliconMarketOverview = marketOverview;
window.SiliconConvergenceEngine = convergenceEngine;

const appScript = document.createElement('script');
appScript.src = new URL('./app.js', import.meta.url).href;
appScript.onerror = () => {
  const app = document.getElementById('app');
  if (app) app.innerHTML = '<div class="boot-screen"><span class="brand-mark">S</span><span>Silicon Terminal could not load its local application script.</span></div>';
};
document.head.append(appScript);
