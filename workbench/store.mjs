import { mkdir, open, readFile, rename, unlink } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { randomUUID } from 'node:crypto';

function validateState(state) {
  if (!state || typeof state !== 'object' || Array.isArray(state)
      || state.schemaVersion !== 1
      || !Array.isArray(state.projects) || !Array.isArray(state.reports)) {
    throw new Error('Invalid or unsupported workbench state; expected schemaVersion 1 with projects and reports arrays');
  }
}

// Reject values JSON would silently discard or change, so disk and memory agree.
function validateJson(value, ancestors = new Set()) {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return;
  if (typeof value === 'number' && Number.isFinite(value)) return;
  if (typeof value !== 'object') {
    throw new TypeError('Workbench state must contain only finite JSON values');
  }
  const prototype = Object.getPrototypeOf(value);
  if (!Array.isArray(value) && prototype !== Object.prototype && prototype !== null) {
    throw new TypeError('Workbench state must contain only plain JSON objects');
  }
  if (ancestors.has(value)) throw new TypeError('Workbench state cannot contain cycles');
  if (Object.getOwnPropertySymbols(value).length) {
    throw new TypeError('Workbench state cannot contain symbol keys');
  }
  ancestors.add(value);
  try {
    if (Array.isArray(value)) {
      if (Object.keys(value).length !== value.length) {
        throw new TypeError('Workbench state arrays cannot have holes or extra properties');
      }
      for (let index = 0; index < value.length; index += 1) {
        if (!Object.hasOwn(value, index)) {
          throw new TypeError('Workbench state arrays cannot have holes');
        }
        validateJson(value[index], ancestors);
      }
    } else {
      for (const entry of Object.values(value)) validateJson(entry, ancestors);
    }
  } finally {
    ancestors.delete(value);
  }
}

async function replaceFile(directory, destination, text) {
  const temporary = join(directory, `.workbench-${randomUUID()}.tmp`);
  let handle;
  let created = false;
  try {
    handle = await open(temporary, 'wx', 0o600);
    created = true;
    await handle.writeFile(text, 'utf8');
    await handle.sync();
    await handle.close();
    handle = undefined;
    // The destination is untouched until this atomic commit point.
    await rename(temporary, destination);
  } finally {
    if (handle) await handle.close().catch(() => {});
    if (created) await unlink(temporary).catch(() => {});
  }
}

export async function openStore({ dataDir } = {}) {
  if (typeof dataDir !== 'string' || dataDir.trim() === '') {
    throw new TypeError('openStore requires a nonempty dataDir');
  }
  const directory = resolve(dataDir);
  const destination = join(directory, 'workbench.json');
  await mkdir(directory, { recursive: true });

  let state = { schemaVersion: 1, projects: [], reports: [] };
  let bytes;
  try {
    bytes = await readFile(destination);
  } catch (error) {
    if (error.code !== 'ENOENT') {
      throw new Error('Could not read workbench.json', { cause: error });
    }
  }
  if (bytes !== undefined) {
    try {
      const text = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
      state = JSON.parse(text);
      validateState(state);
    } catch (error) {
      throw new Error('Cannot open malformed or unsupported workbench.json; original file was preserved', { cause: error });
    }
  }

  let pending = Promise.resolve();
  let closing = false;
  let closePromise;

  return {
    snapshot() {
      return structuredClone(state);
    },

    transact(mutator) {
      if (closing) return Promise.reject(new Error('Workbench store is closed'));
      if (typeof mutator !== 'function') {
        return Promise.reject(new TypeError('Transaction mutator must be a function'));
      }

      const transaction = pending.then(async () => {
        const draft = structuredClone(state);
        const result = mutator(draft);
        if (result && typeof result.then === 'function') {
          // Consume a rejected async result while rejecting this unsupported mutation.
          Promise.resolve(result).catch(() => {});
          throw new TypeError('Transaction mutators must be synchronous');
        }
        validateState(draft);
        validateJson(draft);
        const serialized = `${JSON.stringify(draft, null, 2)}\n`;
        const committed = JSON.parse(serialized);
        const detachedResult = structuredClone(result);

        // Both values are detached before yielding to filesystem operations.
        await replaceFile(directory, destination, serialized);
        state = committed;
        return detachedResult;
      });

      // A failed transaction must not prevent later queued transactions from running.
      pending = transaction.then(() => undefined, () => undefined);
      return transaction;
    },

    close() {
      closing = true;
      closePromise ??= pending;
      return closePromise;
    },
  };
}
