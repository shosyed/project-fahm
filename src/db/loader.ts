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
  const response = await fetch('/quran.db.gz');
  if (!response.ok) {
    throw new Error(`quran.db.gz fetch failed: ${response.status} ${response.statusText}`);
  }
  // Decompress in-browser — quran.db.gz is ~7.6 MB vs 31 MB uncompressed
  const decompressed = response.body!.pipeThrough(new DecompressionStream('gzip'));
  const buf = await new Response(decompressed).arrayBuffer();
  return new SQL.Database(new Uint8Array(buf));
}
