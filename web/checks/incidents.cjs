// Dependency-free checks for saved report selection and export state.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const nodes = new Map();
function element(selector) {
  if (!nodes.has(selector)) nodes.set(selector, {innerHTML:'',textContent:'',hidden:false,disabled:false});
  return nodes.get(selector);
}
const context = vm.createContext({document:{querySelector:element,querySelectorAll:()=>[]},console,encodeURIComponent});
vm.runInContext(fs.readFileSync(path.join(__dirname,'../app.js'),'utf8').replace(/boot\(\);\s*$/,''),context);
vm.runInContext('setViewHash = () => {};',context);
const report = id => ({report_id:id,title:`Report ${id}`,severity:'warning',summary:'Summary',generated_at:'2026-10-22T10:00:00Z',probable_cause:'Investigate configuration',operator_impact:'Checkout degraded',impacted_resource:'payments/deployment/checkout',status_update:'Investigating checkout',timeline:[],next_actions:[]});
(async()=>{
 const calls=[];
 context.apiFetch = async url => {calls.push(url);if(url.includes('limit='))return {reports:[]};return url.endsWith('/markdown') ? '# Saved report' : report('created');};
 await context.createIncidentReport('payments','checkout');
 assert.equal(calls.filter(url=>url.includes('/deployments/')).length,1);
 assert.ok(calls.includes('/api/v1/cluster/incident-reports/created/markdown'));
 assert.equal(element('#downloadIncident').disabled,false);
 assert.equal(element('#incidentMarkdown').textContent,'# Saved report');
 assert.match(element('#incidentList').innerHTML,/No saved reports/);
 // Selecting a newer report must prevent an earlier response overwriting it.
 let finishOld;
 context.apiFetch = url => url.endsWith('/old') ? new Promise(resolve=>{finishOld=()=>resolve(report('old'));}) : Promise.resolve(url.endsWith('/markdown')?'# New':report('new'));
 const old = context.openIncidentReport('old');
 await context.openIncidentReport('new');finishOld();await old;
 assert.equal(element('#incidentTitle').textContent,'Report new');
 // A failed Markdown fetch leaves detail and status available, but disables export.
 context.apiFetch = async url => {if(url.endsWith('/markdown'))throw new Error('Export offline');return report('partial');};
 await context.openIncidentReport('partial');
 assert.equal(element('#copyStatusButton').disabled,false);
 assert.equal(element('#copyMarkdownButton').disabled,true);
 assert.equal(element('#downloadIncident').disabled,true);
 assert.match(element('#incidentFeedback').textContent,/Select this report again/);
 context.apiFetch = async()=>{throw new Error('Not found');};
 await context.openIncidentReport('missing');
 assert.equal(element('#copyStatusButton').disabled,true);
 assert.equal(element('#incidentRoom').hidden,true);
 await context.loadIncidentReports();
 assert.match(element('#incidentList').innerHTML,/Refresh reports to retry/);
 context.apiFetch = async()=>({reports:[{...report('safe'),title:'<script>unsafe</script>'}]});
 await context.loadIncidentReports();
 assert.ok(element('#incidentList').innerHTML.includes('&lt;script&gt;'));
 console.log('Incident checks passed: single creation, same-artifact export, empty list, selection races, partial export failure, missing report, list retry, and escaping.');
})().catch(error=>{console.error(error);process.exitCode=1;});
