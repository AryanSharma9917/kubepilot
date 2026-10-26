const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const nodes = new Map();
function element(selector) {
  if (!nodes.has(selector)) nodes.set(selector,{disabled:false,textContent:''});
  return nodes.get(selector);
}
const context = vm.createContext({document:{querySelector:element,querySelectorAll:()=>[]},console,encodeURIComponent});
vm.runInContext(fs.readFileSync(path.join(__dirname,'../app.js'),'utf8').replace(/boot\(\);\s*$/,''),context);
(async()=>{
 for(const mode of ['fixture','service','kubeconfig','in_cluster']) {
  const requests=[];
  context.apiFetch = async url => {requests.push(url);return url.endsWith('/status')?{kubernetes_mode:mode,cluster_display_name:'Dev east'}:{unhealthy_count:0};};
  await context.checkNamespaceConnection('payments');
  assert.deepEqual(requests,['/api/v1/status','/api/v1/cluster/health?namespace=payments']);
  const text=element('#connectionResult').textContent;
  assert.ok(text.includes('Checked:'));
  assert.ok(text.includes('permissions remain unchecked'));
  if(mode==='fixture')assert.ok(text.includes('No live cluster was checked'));
  if(mode==='service')assert.ok(text.includes('fixture/live mode were not verified'));
 }
 context.apiFetch = async()=>{throw new Error('Forbidden');};
 await context.checkNamespaceConnection('private');
 assert.match(element('#connectionResult').textContent,/RBAC/);
 assert.ok(!element('#connectionResult').textContent.includes('Checked:'));
 assert.equal(element('#connectionForm button').disabled,false);
 console.log('Connection checks passed: namespace-scoped reads, honest fixture/service labels, timestamps, and failure recovery.');
})().catch(error=>{console.error(error);process.exitCode=1;});
