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
  // Dev servers (Vite) set Content-Encoding: gzip, so the browser auto-decompresses
  // the response body before JS sees it. Production (Cloudflare Pages) serves the raw
  // gzip bytes with no Content-Encoding, so we decompress manually. Handle both.
  let buf: ArrayBuffer;
  if (response.headers.get('content-encoding')?.includes('gzip')) {
    buf = await response.arrayBuffer(); // already decompressed by browser
  } else {
    const decompressed = response.body!.pipeThrough(new DecompressionStream('gzip'));
    buf = await new Response(decompressed).arrayBuffer();
  }
  return new SQL.Database(new Uint8Array(buf));
}
