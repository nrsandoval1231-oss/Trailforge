import { createServer } from 'node:http';
import { randomUUID } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createProject, updateProject, appendEvidence, importTrace, buildReport, verifyReport } from './domain.mjs';
import { openStore } from './store.mjs';

const BODY_LIMIT = 256 * 1024;
const ID_PATTERN = /^[a-z0-9][a-z0-9-]{0,63}$/;
const ASSETS = new Map([
  ['/', ['index.html', 'text/html; charset=utf-8']],
  ['/index.html', ['index.html', 'text/html; charset=utf-8']],
  ['/app.js', ['app.js', 'text/javascript; charset=utf-8']],
  ['/styles.css', ['styles.css', 'text/css; charset=utf-8']],
]);

function failure(status, code, message) {
  return Object.assign(new Error(message), { status, code });
}

function validId(id) {
  if (typeof id !== 'string' || !ID_PATTERN.test(id)) {
    throw failure(400, 'INVALID_ID', 'IDs must be lowercase ASCII slugs of 1 to 64 characters.');
  }
  return id;
}

function recordId(body) {
  return validId(body.id === undefined ? randomUUID() : body.id);
}

function findRecord(records, id, kind) {
  const record = records.find((item) => item.id === id);
  if (!record) throw failure(404, 'NOT_FOUND', `${kind} was not found.`);
  return record;
}

function ensureUnique(records, id) {
  if (records.some((item) => item.id === id)) {
    throw failure(409, 'DUPLICATE_ID', 'That ID already exists. Choose a different ID.');
  }
}

function json(response, status, body, headers = {}) {
  const bytes = Buffer.from(JSON.stringify(body), 'utf8');
  response.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
    'Content-Length': bytes.length,
    ...headers,
  });
  response.end(bytes);
}

async function readJson(request) {
  const mediaType = request.headers['content-type'] || '';
  if (!/^application\/json(?:\s*;\s*charset\s*=\s*(?:utf-8|"utf-8"))?\s*$/i.test(mediaType)) {
    request.resume();
    throw failure(400, 'INVALID_CONTENT_TYPE', 'Send application/json with an optional UTF-8 charset.');
  }
  if (Number(request.headers['content-length']) > BODY_LIMIT) {
    request.resume();
    throw failure(413, 'BODY_TOO_LARGE', 'JSON request bodies must not exceed 256 KiB.');
  }
  const bytes = await new Promise((resolveBody, rejectBody) => {
    const chunks = [];
    let size = 0;
    let rejected = false;
    request.on('data', (chunk) => {
      if (rejected) return;
      size += chunk.length;
      if (size > BODY_LIMIT) {
        rejected = true;
        chunks.length = 0;
        rejectBody(failure(413, 'BODY_TOO_LARGE', 'JSON request bodies must not exceed 256 KiB.'));
        return;
      }
      chunks.push(chunk);
    });
    request.on('end', () => {
      if (!rejected) resolveBody(Buffer.concat(chunks));
    });
    request.on('aborted', () => rejectBody(failure(400, 'INCOMPLETE_BODY', 'The request body was interrupted.')));
    request.on('error', () => rejectBody(failure(400, 'INVALID_BODY', 'The request body could not be read.')));
  });
  let body;
  try {
    body = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
  } catch {
    throw failure(400, 'INVALID_JSON', 'Send a valid UTF-8 JSON object.');
  }
  if (body === null || typeof body !== 'object' || Array.isArray(body)) {
    throw failure(400, 'INVALID_BODY', 'The request body must be a JSON object.');
  }
  return body;
}

function verificationFor(report) {
  try {
    return verifyReport(report);
  } catch {
    return {
      integrity: 'FAIL',
      replay: 'FAIL',
      checks: { inputHash: false, resultHash: false, recomputedResult: false },
    };
  }
}

function verified(report) {
  const verification = verificationFor(report);
  if (verification.integrity !== 'PASS' || verification.replay !== 'PASS') {
    throw failure(422, 'REPORT_INTEGRITY_FAILED', 'The frozen report failed integrity or replay verification. Its retained artifact has not been changed.');
  }
  return verification;
}

function compareText(a, b) {
  return a < b ? -1 : a > b ? 1 : 0;
}

export async function startServer(options = {}) {
  const requestedPort = options.port ?? process.env.PORT ?? 3000;
  if (!/^[0-9]+$/.test(String(requestedPort)) || !Number.isInteger(Number(requestedPort)) || Number(requestedPort) > 65535) {
    throw failure(400, 'INVALID_PORT', 'PORT must be an integer from 0 to 65535.');
  }
  const dataDir = options.dataDir ?? process.env.DATA_DIR ?? './data';
  const store = await openStore({ dataDir });
  let url;

  async function api(request, response, parsed) {
    const method = request.method;
    const pathname = parsed.pathname;
    const mutation = !['GET', 'HEAD', 'OPTIONS'].includes(method);
    if (mutation && request.headers.origin !== undefined && request.headers.origin !== url) {
      request.resume();
      throw failure(403, 'CROSS_ORIGIN', 'Mutation requests must originate from this workbench.');
    }

    if (pathname === '/api/projects' && method === 'GET') {
      const query = (parsed.searchParams.get('q') || '').toLowerCase();
      const includeArchived = parsed.searchParams.get('includeArchived') === 'true';
      const projects = store.snapshot().projects
        .filter((project) => (includeArchived || !project.archived)
          && [project.name, project.location, project.notes].some((value) => value.toLowerCase().includes(query)))
        .sort((a, b) => compareText(a.name, b.name) || compareText(a.id, b.id));
      return json(response, 200, { projects });
    }

    if ((pathname === '/api/projects' || pathname === '/api/imports/traces') && method === 'POST') {
      const body = await readJson(request);
      const id = recordId(body);
      const project = await store.transact((state) => {
        ensureUnique(state.projects, id);
        const input = { ...body, id };
        const now = new Date().toISOString();
        const created = pathname === '/api/projects'
          ? createProject(input, { now })
          : importTrace(input, { now });
        state.projects.push(created);
        return created;
      });
      return json(response, 201, { project });
    }

    const projectRoute = /^\/api\/projects\/([^/]+)(\/evidence)?$/.exec(pathname);
    if (projectRoute) {
      const id = decodeId(projectRoute[1]);
      const evidenceRoute = Boolean(projectRoute[2]);
      if (!evidenceRoute && method === 'GET') {
        return json(response, 200, { project: findRecord(store.snapshot().projects, id, 'Project') });
      }
      if ((!evidenceRoute && ['PATCH', 'DELETE'].includes(method)) || (evidenceRoute && method === 'POST')) {
        const body = await readJson(request);
        if (method === 'DELETE' && Object.keys(body).some((key) => key !== 'revision')) {
          throw failure(400, 'INVALID_BODY', 'Archiving accepts only the current revision.');
        }
        const evidenceId = evidenceRoute ? recordId(body) : undefined;
        const project = await store.transact((state) => {
          const current = findRecord(state.projects, id, 'Project');
          const now = new Date().toISOString();
          let next;
          if (evidenceRoute) {
            if (body.revision !== current.revision) {
              throw failure(409, 'STALE_REVISION', 'The project changed. Reload it before appending evidence.');
            }
            ensureUnique(current.evidence, evidenceId);
            next = appendEvidence(current, { ...body, id: evidenceId }, { now });
          } else {
            const patch = method === 'DELETE' ? { revision: body.revision, archived: true } : body;
            next = updateProject(current, patch, { now });
          }
          state.projects[state.projects.findIndex((item) => item.id === id)] = next;
          return next;
        });
        return json(response, evidenceRoute ? 201 : 200, { project });
      }
    }

    if (pathname === '/api/reports' && method === 'GET') {
      const reports = store.snapshot().reports
        .sort((a, b) => compareText(b.createdAt, a.createdAt) || compareText(a.id, b.id))
        .map((report) => ({
          id: report.id,
          name: report.name,
          createdAt: report.createdAt,
          summary: report.summary,
          integrity: verificationFor(report).integrity,
        }));
      return json(response, 200, { reports });
    }

    if (pathname === '/api/reports' && method === 'POST') {
      const body = await readJson(request);
      const id = recordId(body);
      if (!Array.isArray(body.projectIds) || body.projectIds.length < 1 || body.projectIds.length > 50
        || new Set(body.projectIds).size !== body.projectIds.length) {
        throw failure(400, 'INVALID_PROJECT_SELECTION', 'Select 1 to 50 distinct active projects.');
      }
      body.projectIds.forEach(validId);
      const report = await store.transact((state) => {
        ensureUnique(state.reports, id);
        const projects = body.projectIds.map((projectId) => {
          const project = state.projects.find((item) => item.id === projectId);
          if (!project || project.archived) {
            throw failure(400, 'INVALID_PROJECT_SELECTION', 'Every selected project must exist and be active.');
          }
          return project;
        });
        const created = buildReport(projects, { id, name: body.name, now: new Date().toISOString() });
        verified(created);
        state.reports.push(created);
        return created;
      });
      return json(response, 201, { report });
    }

    const reportRoute = /^\/api\/reports\/([^/]+)(\/(?:replay|export))?$/.exec(pathname);
    if (reportRoute) {
      const id = decodeId(reportRoute[1]);
      const action = reportRoute[2] || '';
      if ((method === 'GET' && (action === '' || action === '/export')) || (method === 'POST' && action === '/replay')) {
        if (action === '/replay') {
          const body = await readJson(request);
          if (Object.keys(body).length !== 0) {
            throw failure(400, 'INVALID_BODY', 'Replay accepts an empty JSON object.');
          }
        }
        const report = findRecord(store.snapshot().reports, id, 'Report');
        const verification = verified(report);
        if (action === '/replay') return json(response, 200, verification);
        if (action === '/export') {
          return json(response, 200, report, { 'Content-Disposition': `attachment; filename="${id}.json"` });
        }
        return json(response, 200, { report, verification });
      }
    }
    throw failure(404, 'NOT_FOUND', 'This API route does not exist.');
  }

  const server = createServer(async (request, response) => {
    try {
      const parsed = new URL(request.url, 'http://127.0.0.1');
      if (parsed.pathname === '/api' || parsed.pathname.startsWith('/api/')) {
        await api(request, response, parsed);
        return;
      }
      const asset = ASSETS.get(parsed.pathname);
      if (!asset || !['GET', 'HEAD'].includes(request.method)) {
        throw failure(404, 'NOT_FOUND', 'This resource does not exist.');
      }
      let bytes;
      try {
        bytes = await readFile(new URL(`./public/${asset[0]}`, import.meta.url));
      } catch (error) {
        if (error.code === 'ENOENT' || error.code === 'ENOTDIR') {
          throw failure(404, 'NOT_FOUND', 'This application asset is not available.');
        }
        throw error;
      }
      response.writeHead(200, {
        'Content-Type': asset[1],
        'Content-Length': bytes.length,
        'Cache-Control': 'no-cache',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer',
        'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
      });
      response.end(request.method === 'HEAD' ? undefined : bytes);
    } catch (error) {
      if (response.destroyed || response.writableEnded) return;
      if (response.headersSent) {
        response.destroy();
        return;
      }
      const status = [400, 403, 404, 409, 413, 422].includes(error.status) ? error.status : 500;
      json(response, status, {
        error: status === 500
          ? 'The workbench could not complete the request. Check local storage availability and retry.'
          : error.message,
        code: status === 500 ? 'INTERNAL_ERROR' : (error.code || 'VALIDATION_ERROR'),
      });
    }
  });
  server.requestTimeout = 30000;
  server.headersTimeout = 15000;

  try {
    await new Promise((resolveListening, rejectListening) => {
      const onError = (error) => rejectListening(error);
      server.once('error', onError);
      server.listen(Number(requestedPort), '127.0.0.1', () => {
        server.off('error', onError);
        url = `http://127.0.0.1:${server.address().port}`;
        resolveListening();
      });
    });
  } catch (error) {
    await store.close();
    throw error;
  }

  let closing;
  function close() {
    if (!closing) {
      closing = (async () => {
        try {
          await new Promise((resolveClosed, rejectClosed) => {
            server.close((error) => error ? rejectClosed(error) : resolveClosed());
            server.closeIdleConnections();
          });
        } finally {
          await store.close();
        }
      })();
    }
    return closing;
  }
  return { url, close };
}

function decodeId(segment) {
  let id;
  try {
    id = decodeURIComponent(segment);
  } catch {
    throw failure(400, 'INVALID_ID', 'The resource ID has invalid URL encoding.');
  }
  return validId(id);
}

if (process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url) {
  try {
    const app = await startServer();
    console.log(app.url);
    const shutdown = () => {
      app.close().catch(() => {
        console.error('Could not close the workbench cleanly. Check local storage availability.');
        process.exitCode = 1;
      });
    };
    process.once('SIGINT', shutdown);
    process.once('SIGTERM', shutdown);
  } catch {
    console.error('Could not start the workbench. Check PORT, DATA_DIR, and the retained workbench.json file.');
    process.exitCode = 1;
  }
}
