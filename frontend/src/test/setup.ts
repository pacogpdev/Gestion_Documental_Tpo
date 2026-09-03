import '@testing-library/jest-dom';
import { server } from '../mocks/server';

const storage = new Map<string, string>();
const localStorageShim: Storage = {
  get length() { return storage.size; },
  clear: () => storage.clear(),
  getItem: (key) => storage.get(String(key)) ?? null,
  key: (index) => Array.from(storage.keys())[index] ?? null,
  removeItem: (key) => { storage.delete(String(key)); },
  setItem: (key, value) => { storage.set(String(key), String(value)); },
};

Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: localStorageShim });
Object.defineProperty(window, 'localStorage', { configurable: true, value: localStorageShim });

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
