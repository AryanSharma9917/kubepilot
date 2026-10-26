const {test} = require('node:test');
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {once} = require('node:events');
const {existsSync} = require('node:fs');
const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const {chromium} = require('playwright');
const {createDevServer} = require('../dev-server.cjs');
const root = path.resolve(__dirname, '../..');
async function unusedPort() {
  const server = http.createServer();
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  const port = server.address().port; await new Promise(resolve => server.close(resolve));
  return port;
}
async function waitForApi(url, process) {
  const deadline = Date.now() + 20000;
  while (Date.now() < deadline) {
    if (!process.pid || process.exitCode !== null) throw new Error(`Fixture API exited with ${process.exitCode}`);
    try {if ((await fetch(`${url}/healthz`)).ok) return;} catch {}
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error('Fixture API did not become healthy');
}
test('guided fixture demo in a real browser', {timeout:120000}, async t => {
  const port = await unusedPort();
  const apiUrl = `http://127.0.0.1:${port}`;
  const python = process.env.KUBEPILOT_PYTHON || (existsSync(path.join(root,'.venv/bin/python')) ? path.join(root,'.venv/bin/python') : 'python3');
  const api = spawn(python, ['-m','uvicorn','kubepilot_api.main:app','--host','127.0.0.1','--port',String(port)], {
    cwd:root, stdio:['ignore','ignore','pipe'], env:{...process.env,
      KUBEPILOT_ENVIRONMENT:'development', KUBEPILOT_K8S_MODE:'fixture',
      KUBEPILOT_DATABASE_URL:'', KUBEPILOT_LLM_PROVIDER:'deterministic',
      KUBEPILOT_AGENT_MODE:'deterministic', KUBEPILOT_RAG_MODE:'keyword',
      KUBEPILOT_API_KEYS:'', KUBEPILOT_OIDC_ISSUER:'', KUBEPILOT_OIDC_REQUIRED:'false',
      KUBEPILOT_ALLOWED_NAMESPACES:'', KUBEPILOT_ALLOWED_ACTIONS:'',
      KUBEPILOT_RATE_LIMIT_PER_MINUTE:'0', KUBEPILOT_OTEL_EXPORTER_OTLP_ENDPOINT:'',
    },
  });
  api.stderr.resume();
  let spawnError;
  api.on('error', error => {spawnError = error;});
  const server = createDevServer(apiUrl);
  let browser;
  try {
    await waitForApi(apiUrl, api);
    if (spawnError) throw spawnError;
    server.listen(0,'127.0.0.1');await once(server,'listening');
    const base = `http://127.0.0.1:${server.address().port}`;
    browser = await chromium.launch({headless:true,
      ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH} : {}),
    });
    await t.test('all fixture scenarios, contextual chat, and same-artifact handoff', async () => {
      const context = await browser.newContext({permissions:['clipboard-read','clipboard-write']});
      try {
        const page = await context.newPage();const errors=[];
        page.on('pageerror', error => errors.push(error.message));
        await page.goto(base);await page.getByText('API connected',{exact:true}).waitFor();
        const reports = () => fetch(`${apiUrl}/api/v1/cluster/incident-reports`).then(r=>r.json());
        assert.equal((await reports()).reports.length,0);
        for (const [namespace, deployment] of [['payments','checkout'],['platform','metrics-scraper'],['notifications','email-worker']]) {
          await page.getByRole('button',{name:'Overview',exact:true}).click();
          await page.getByRole('button',{name:`Investigate ${namespace}/${deployment}`,exact:true}).click();
          await page.getByRole('heading',{name:'5. Verify the outcome'}).waitFor();
          assert.equal(await page.locator('#deploymentInput').inputValue(),deployment);
          assert.equal((await reports()).reports.length,0,'Diagnosis must not create artifacts');
        }
        await page.getByRole('button',{name:'Ask about this workload',exact:true}).click();
        await page.getByRole('button',{name:'Explain this failure',exact:true}).click();
        await page.waitForFunction(()=>document.querySelectorAll('.chat-answer').length===1);
        assert.match(await page.locator('.chat-answer').textContent(),/notifications\/deployment\/email-worker/);
        await page.getByRole('button',{name:'Clear workload context',exact:true}).click();
        assert.equal(await page.getByRole('button',{name:'Explain this failure',exact:true}).isDisabled(),true);
        await page.getByRole('button',{name:'Explain image pull failures',exact:true}).click();
        await page.locator('.citation-list').waitFor();
        await page.getByRole('button',{name:'Workloads',exact:true}).click();
        await page.getByRole('button',{name:'Create incident report',exact:true}).click();
        await page.waitForFunction(()=>document.querySelector('#incidentFeedback').textContent.includes('Ready to copy'));
        const saved = (await reports()).reports;assert.equal(saved.length,1);const id=saved[0].report_id;
        await page.getByRole('button',{name:'Copy status update',exact:true}).click();
        await page.getByText('Status update copied.',{exact:true}).waitFor();
        assert.match(await page.evaluate(()=>navigator.clipboard.readText()),/email-worker/);
        const downloadPromise=page.waitForEvent('download');
        await page.getByRole('button',{name:'Download Markdown',exact:true}).click();
        const download=await downloadPromise;assert.ok(download.suggestedFilename().includes(id));
        assert.ok((await fs.readFile(await download.path(),'utf8')).includes(id));
        assert.equal((await reports()).reports.length,1);
        await page.reload();await page.locator('[data-incident-id]').first().click();
        await page.waitForFunction(()=>!document.querySelector('#downloadIncident').disabled);
        for (const theme of ['light','dark']) {
          await page.evaluate(value=>{localStorage.setItem('kubepilot-theme',value);document.body.dataset.theme=value;},theme);
          for(const width of [1440,390]) {
            await page.setViewportSize({width,height:900});
            for (const [label,view] of [['Overview','dashboard'],['Workloads','diagnosis'],['Ask KubePilot','copilot'],['Incidents','incident']]) {
              if(label==='Ask KubePilot') await page.locator('.sidebar-tools').evaluate(e=>{e.open=true;});
              await page.getByRole('button',{name:label,exact:true}).click();
              assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`${view} overflow at ${width} in ${theme}`);
              if(process.env.KUBEPILOT_SCREENSHOT_DIR) {
                await fs.mkdir(process.env.KUBEPILOT_SCREENSHOT_DIR,{recursive:true});
                await page.screenshot({path:path.join(process.env.KUBEPILOT_SCREENSHOT_DIR,`${view}-${theme}-${width}.png`),fullPage:true});
              }
            }
          }
        }
        assert.deepEqual(errors,[]);
      } finally {await context.close();}
    });
    await t.test('guided namespace check never labels fixtures as a live cluster', async () => {
      const context=await browser.newContext();
      try {
        const page=await context.newPage();await page.goto(base);
        await page.locator('.sidebar-tools').evaluate(e=>{e.open=true;});
        await page.getByRole('button',{name:'Cluster connection',exact:true}).click();
        await page.locator('#connectionNamespace').fill('payments');
        await page.getByRole('button',{name:'Check namespace access',exact:true}).click();
        await page.getByText(/No live cluster was checked/).waitFor();
        assert.match(await page.locator('#connectionResult').textContent(),/Namespace: payments/);
        await page.route('**/api/v1/cluster/health?namespace=*',r=>r.fulfill({status:403,contentType:'application/json',body:JSON.stringify({detail:'Namespace is not allowed'})}));
        await page.getByRole('button',{name:'Check namespace access',exact:true}).click();
        await page.getByText(/Namespace check failed/).waitFor();
        assert.ok(!(await page.locator('#connectionResult').textContent()).includes('Checked:'));
        await page.setViewportSize({width:390,height:900});
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
      } finally {await context.close();}
    });
    await t.test('keyboard entry, history, invalid hashes, and reduced motion', async () => {
      const context=await browser.newContext({reducedMotion:'reduce'});
      try {
        const page=await context.newPage();await page.goto(base);
        await page.keyboard.press('Tab');assert.equal(await page.locator('.skip-link').evaluate(e=>e===document.activeElement),true);
        await page.keyboard.press('Enter');assert.equal(await page.locator('#mainContent').evaluate(e=>e===document.activeElement),true);
        await page.getByRole('button',{name:'Workloads',exact:true}).focus();await page.keyboard.press('Enter');
        assert.equal(await page.getByRole('heading',{name:'Workload investigation',exact:true}).evaluate(e=>e===document.activeElement),true);
        await page.getByRole('button',{name:'Overview',exact:true}).click();await page.goBack();
        await page.locator('[data-view-panel="diagnosis"].active').waitFor();
        await page.goto(`${base}/#%22%5Dinvalid`);
        await page.locator('[data-view-panel="dashboard"].active').waitFor();
        assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).scrollBehavior),'auto');
      } finally {await context.close();}
    });
    await t.test('optional activity failures, workload retry, and missing deployment', async () => {
      const context=await browser.newContext();
      try {
        const page=await context.newPage();
        await page.route('**/api/v1/traces?*',r=>r.fulfill({status:503,body:'Unavailable'}));
        await page.route('**/api/v1/audit/events?*',r=>r.fulfill({status:503,body:'Unavailable'}));
        await page.goto(base);await page.getByText('API connected',{exact:true}).waitFor();
        assert.equal(await page.locator('.workload-action').count(),3);
        await page.route('**/api/v1/cluster/health',r=>r.fulfill({status:503,body:'Unavailable'}));
        await page.getByRole('button',{name:'Refresh cluster signals',exact:true}).click();
        await page.getByText('Some data unavailable',{exact:true}).waitFor();
        assert.match(await page.locator('#workloadList').textContent(),/select Refresh/);
        await page.unroute('**/api/v1/cluster/health');await page.getByRole('button',{name:'Refresh cluster signals',exact:true}).click();
        await page.getByText('API connected',{exact:true}).waitFor();
        await page.getByRole('button',{name:'Workloads',exact:true}).click();
        await page.getByLabel('Namespace',{exact:true}).fill('payments');await page.getByLabel('Deployment',{exact:true}).fill('missing');
        await page.getByRole('button',{name:'Investigate workload',exact:true}).click();
        await page.locator('#diagnosisOutput [role="alert"]').waitFor();
        assert.match(await page.locator('#diagnosisOutput').textContent(),/Check the workload names/);
      } finally {await context.close();}
    });
  } finally {
    if(browser)await browser.close();
    server.closeAllConnections();await new Promise(resolve=>server.close(resolve));
    if(api.pid && api.exitCode===null){const exited=once(api,'exit');api.kill('SIGTERM');await exited;}
  }
});
