import { useState, useEffect } from 'react';
import type { Database } from 'sql.js';
import { getDb } from './loader.ts';

type DbState =
  | { status: 'loading' }
  | { status: 'error'; error: Error }
  | { status: 'ready'; db: Database };

export function useDb(): DbState {
  const [state, setState] = useState<DbState>({ status: 'loading' });
  useEffect(() => {
    getDb()
      .then(db => setState({ status: 'ready', db }))
      .catch((err: unknown) => setState({ status: 'error', error: err instanceof Error ? err : new Error(String(err)) }));
  }, []);
  return state;
}
