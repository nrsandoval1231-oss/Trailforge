import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile, readdir, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { openStore } from '../workbench/store.mjs';

test('durable transactions serialize, detach snapshots, abort on errors, and survive restart', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'trailforge-store-'));
  let store;
  try {
    store = await openStore({ dataDir: directory });
    assert.deepEqual(store.snapshot(), { schemaVersion: 1, projects: [], reports: [] });
    await Promise.all(Array.from({ length: 8 }, (_, index) => store.transact(state => {
      state.projects.push({ id: `test-${index}`, name: `Test ${index}` });
      return { count: state.projects.length };
    })));
    assert.equal(store.snapshot().projects.length, 8);
    const detached = store.snapshot();
    detached.projects[0].name = 'Mutated snapshot';
    assert.equal(store.snapshot().projects[0].name, 'Test 0');
    await assert.rejects(store.transact(state => {
      state.projects = [];
      throw new Error('Abort this transaction');
    }), /Abort this transaction/);
    assert.equal(store.snapshot().projects.length, 8);
    await store.close();
    store = await openStore({ dataDir: directory });
    assert.deepEqual(store.snapshot().projects.map(project => project.id), Array.from({ length: 8 }, (_, index) => `test-${index}`));
    const persisted = JSON.parse(await readFile(join(directory, 'workbench.json'), 'utf8'));
    assert.deepEqual(persisted, store.snapshot());
    assert.deepEqual((await readdir(directory)).filter(name => name.endsWith('.tmp')), []);
  } finally {
    if (store) await store.close();
    await rm(directory, { recursive: true, force: true });
  }
});

test('corrupt persisted state fails without destroying its original bytes', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'trailforge-corrupt-'));
  const path = join(directory, 'workbench.json');
  try {
    for (const raw of ['{broken', JSON.stringify({ schemaVersion: 999, projects: [], reports: [] })]) {
      await writeFile(path, raw);
      await assert.rejects(openStore({ dataDir: directory }));
      assert.equal(await readFile(path, 'utf8'), raw);
    }
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
