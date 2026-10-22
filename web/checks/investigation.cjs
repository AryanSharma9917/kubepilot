// Dependency-free checks for investigation rendering and overlapping requests.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const nodes = new Map();
function element(selector) {
  if (!nodes.has(selector)) nodes.set(selector, {
    value: '', innerHTML: '', textContent: '', disabled: false,
    querySelector: child => element(`${selector} ${child}`),
  });
  return nodes.get(selector);
}
const context = vm.createContext({
  document: {querySelector: element, querySelectorAll: () => []},
  console, encodeURIComponent,
});
const source = fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8');
vm.runInContext(source.replace(/boot\(\);\s*$/, ''), context);
vm.runInContext(`
  setViewHash = () => {};
  loadOverview = async () => {};
  renderIncidentReport = () => {};
  renderIncidentError = () => {};
`, context);
const diagnosis = {
  namespace: 'payments', name: 'checkout',
  health: {status: 'Degraded', reason: 'Two unavailable replicas'},
  pods: [], events: [], logs: [], recommendations: ['Inspect previous logs'],
};
context.diagnosisFixture = diagnosis;
vm.runInContext(`renderDiagnosis(diagnosisFixture, null, {probable_cause: '<script>unsafe</script>'})`, context);
const html = element('#diagnosisOutput').innerHTML;
for (const heading of ['Observed problem', 'Likely cause', 'Evidence', 'Next checks', 'Verify the outcome']) assert.ok(html.includes(heading));
assert.ok(html.includes('&lt;script&gt;unsafe&lt;/script&gt;'));
assert.ok(!html.includes('<script>'));
assert.ok(html.includes('Demo fixtures stay unhealthy'));
vm.runInContext(`
  namespaceInput.value = 'payments'; deploymentInput.value = 'checkout';
  renderWorkloads({workloads: [{namespace:'payments',name:'checkout',reason:'Unavailable',kind:'Deployment',ready_replicas:1,desired_replicas:3}]});
`, context);
assert.equal(element('#workloadSelect').value, '0');
vm.runInContext('renderWorkloads({workloads: []})', context);
assert.match(element('#workloadList').innerHTML, /No unhealthy workloads/);
(async () => {
  // Hold the first investigation while the second completes, then release it.
  const pending = [];
  context.apiFetch = url => url.includes('/old/')
    ? new Promise(resolve => pending.push(() => resolve(diagnosis)))
    : Promise.resolve(url.endsWith('/diagnose') ? {...diagnosis, name:'new'} : url.endsWith('/remediation-plan') ? null : {});
  const first = context.diagnoseDeployment('payments', 'old');
  await context.diagnoseDeployment('payments', 'new');
  const newest = element('#diagnosisOutput').innerHTML;
  pending.forEach(resolve => resolve());
  await first;
  assert.equal(element('#diagnosisOutput').innerHTML, newest);
  assert.match(newest, /payments\/deployment\/new/);
  assert.equal(element('#deploymentInput').value, 'new');
  context.apiFetch = async () => { throw new Error('Not found'); };
  await context.diagnoseDeployment('payments', 'missing');
  assert.match(element('#diagnosisOutput').innerHTML, /Check the workload names/);
  assert.equal(element("#diagnosisForm button[type='submit']").disabled, false);
  console.log('Investigation checks passed: guided rendering, escaping, selector, empty state, stale response protection, and retry state.');
})().catch(error => {console.error(error); process.exitCode = 1;});
