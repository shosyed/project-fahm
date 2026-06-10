import initSqlJs from 'sql.js';
import type { Database } from 'sql.js';

let _dbPromise: Promise<Database> | null = null;

export function getDb(): Promise<Database> {
  if (!_dbPromise) {
    _dbPromise = _init();
  }
  return _dbPromise;
}

async function _init(): Promise<Database> {
  const SQL = await initSqlJs({
    locateFile: () => '/sql-wasm.wasm',
  });
  const response = await fetch('/quran.db');
  if (!response.ok) {
    throw new Error(`quran.db fetch failed: ${response.status} ${response.statusText}`);
  }
  const buf = await response.arrayBuffer();
  return new SQL.Database(new Uint8Array(buf));
}
