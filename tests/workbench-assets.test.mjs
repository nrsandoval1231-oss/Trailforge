import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { startServer } from '../workbench/server.mjs';

test('the served workbench has local executable assets, stable controls, and safe route boundaries', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'trailforge-assets-'));
  let app;
  try {
    app = await startServer({ port: 0, dataDir: directory });
    const page = await fetch(app.url + '/');
    assert.equal(page.status, 200);
    assert.match(page.headers.get('content-type'), /text\/html/);
    const html = await page.text();
    assert.match(html, /lang="en"/);
    assert.match(html, /name="viewport"/);
    assert.match(html, /TrailForge/i);
    assert.match(html, /src="\/app\.js"/);
    assert.match(html, /href="\/styles\.css"/);
    assert.doesNotMatch(html, /<script\b[^>]*>\s*[^<\s]/i);
    assert.doesNotMatch(html, /(?:src|href)="https?:\/\//i);
    const script = await fetch(app.url + '/app.js');
    assert.equal(script.status, 200);
    assert.match(script.headers.get('content-type'), /javascript/);
    const js = await script.text();
    assert.doesNotMatch(js, /innerHTML|insertAdjacentHTML|document\.write\s*\(/);
    const css = await fetch(app.url + '/styles.css');
    assert.equal(css.status, 200);
    assert.match(css.headers.get('content-type'), /text\/css/);
    const styles = await css.text();
    assert.match(styles, /@media/);
    assert.match(styles, /focus-visible/);
    assert.match(styles, /prefers-reduced-motion/);
    const controls = ['new-project', 'project-list', 'project-search', 'project-dialog', 'project-name-input', 'project-location-input', 'project-notes-input', 'save-project', 'project-form-error', 'edit-project', 'archive-dialog', 'confirm-archive', 'cancel-archive', 'show-archived', 'add-evidence', 'evidence-title', 'evidence-excerpt', 'evidence-quote', 'save-evidence', 'run-project-report', 'report-result', 'verify-replay', 'replay-status'];
    for (const control of controls) assert.ok((html + js).includes(control), `Missing stable UI selector ${control}`);
    for (const path of ['/missing.js', '/workbench/server.mjs', '/%2e%2e/package.json']) {
      const missing = await fetch(app.url + path);
      assert.equal(missing.status, 404);
    }
    const created = await fetch(app.url + '/api/projects', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: 'asset-journey', name: '<img src=x onerror=alert(1)> research note' }) });
    assert.equal(created.status, 201);
    const listing = await fetch(app.url + '/api/projects?q=research');
    assert.equal((await listing.json()).projects[0].name, '<img src=x onerror=alert(1)> research note');
    const instructions = await readFile(new URL('../workbench/README.md', import.meta.url), 'utf8');
    assert.match(instructions, /node --test/);
    assert.match(instructions, /DATA_DIR/);
    assert.match(instructions, /PORT/);
  } finally {
    if (app) await app.close();
    await rm(directory, { recursive: true, force: true });
  }
});
