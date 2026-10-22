// Run with node web/checks/chat.cjs; no third-party dependencies required.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const nodes = new Map();
function element(selector) {
  if (!nodes.has(selector)) nodes.set(selector, {
    value: '', innerHTML: '', textContent: '', style: {}, hidden: false,
    querySelector: child => element(`${selector} ${child}`), focus() {},
  });
  return nodes.get(selector);
}
const context = vm.createContext({
  document: {querySelector: element, querySelectorAll: () => []},
  console, encodeURIComponent, performance: {now: () => Infinity},
});
vm.runInContext(fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8').replace(/boot\(\);\s*$/, ''), context);
vm.runInContext(`setViewHash = () => {}; loadOverview = async () => {}; appendChatMessage = () => {}; replacePendingAssistant = () => {};`, context);
(async () => {
  let release;
  const requests = [];
  context.apiFetch = (url, options) => {
    requests.push(JSON.parse(options.body));
    return new Promise(resolve => {release = () => resolve({answer: 'Summary: Reviewed', sources: [], citations: []});});
  };
  vm.runInContext(`chatWorkload = {namespace:'payments', deployment:'checkout'}; updateChatContext();`, context);
  assert.match(element('#chatWorkloadContext').textContent, /payments\/checkout/);
  const first = context.sendChat('Why is this failing?');
  await context.sendChat('Duplicate click');
  assert.equal(requests.length, 1);
  vm.runInContext('chatWorkload = null; updateChatContext();', context);
  assert.equal(requests[0].workload.deployment, 'checkout');
  release(); await first;
  assert.equal(element('#chatInput').disabled, false);
  const second = context.sendChat('General question');
  assert.equal(requests[1].workload, undefined);
  release(); await second;
  context.apiFetch = async () => {throw new Error('Offline');};
  await context.sendChat('Retry after failure');
  assert.equal(element("#chatForm button[type='submit']").disabled, false);
  const html = context.renderChatAnswer({
    answer:'Evidence: <img src=x onerror=alert(1)>\nNext actions: Inspect logs',
    sources:['Runbook title'], citations:[],
    workflow_steps:[{name:'inspect',description:'Reviewed evidence',status:'completed'}],
  });
  assert.ok(html.includes('Observed evidence:'));
  assert.ok(html.includes('Suggested next checks:'));
  assert.ok(!html.includes('<img'));
  assert.ok(html.includes('No runbook excerpts'));
  assert.ok(html.includes('<details class="workflow-panel">'));
  assert.match(element('#retrievedSources').innerHTML, /No supporting excerpt/);
  const commands = context.buildDiagnosisCommands({namespace:'payments',name:'checkout',pods:[]});
  assert.ok(commands.every(command => command.description.length > 20));
  console.log('Chat checks passed: explicit context, clearing, duplicate submission, failure recovery, escaped evidence, honest sources, and explained commands.');
})().catch(error => {console.error(error);process.exitCode = 1;});
