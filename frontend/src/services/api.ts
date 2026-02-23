// Shim — all exports live in ./api/index.ts
// This file exists only so that existing `import ... from '../services/api'` calls
// continue to resolve without any changes to callers.
export * from './api/index';
