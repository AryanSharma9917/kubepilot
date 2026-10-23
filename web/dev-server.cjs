// Local development only. Serve the static UI and proxy the native FastAPI app.
const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');
const assets = new Map([
  ['/','index.html'], ['/index.html','index.html'], ['/app.js','app.js'],
  ['/styles.css','styles.css'], ['/kubepilot-icon.svg','kubepilot-icon.svg'],
]);
const mime = {'.html':'text/html', '.js':'text/javascript', '.css':'text/css', '.svg':'image/svg+xml'};
function createDevServer(apiUrl = 'http://127.0.0.1:8000') {
  const base = new URL(apiUrl);
  if (base.protocol !== 'http:') throw new Error('The native development API URL must use http:');
  return http.createServer(async (req, res) => {
    let url;
    try {url = new URL(req.url, 'http://localhost');}
    catch {res.writeHead(400);res.end('Bad request');return;}
    if (url.pathname.startsWith('/api/') || ['/healthz','/readyz','/metrics'].includes(url.pathname)) {
      const upstream = http.request(new URL(`${url.pathname}${url.search}`, base), {
        method:req.method, headers:{...req.headers, host:base.host},
      }, response => {res.writeHead(response.statusCode, response.headers); response.pipe(res);});
      upstream.setTimeout(15000, () => upstream.destroy(new Error('API request timed out')));
      upstream.on('error', () => {
        if (!res.headersSent) res.writeHead(502, {'content-type':'application/json'});
        res.end(JSON.stringify({detail:'Development API unavailable. Start the FastAPI server and retry.'}));
      });
      req.on('aborted', () => upstream.destroy());
      req.pipe(upstream);
      return;
    }
    const asset = assets.get(url.pathname);
    if (!asset || !['GET','HEAD'].includes(req.method)) {res.writeHead(404);res.end('Not found');return;}
    try {
      const body = await fs.readFile(path.join(__dirname, asset));
      res.writeHead(200, {'content-type':mime[path.extname(asset)], 'cache-control':'no-store'});
      res.end(req.method === 'HEAD' ? undefined : body);
    } catch {
      res.writeHead(404);res.end('Not found');
    }
  });
}
if (require.main === module) {
  const port = Number(process.env.KUBEPILOT_WEB_PORT || 3000);
  createDevServer(process.env.KUBEPILOT_API_URL).listen(port, '127.0.0.1', () => {
    console.log(`KubePilot development UI listening on port ${port}`);
  });
}
module.exports = {createDevServer};
