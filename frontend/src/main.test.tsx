import { beforeEach, describe, expect, it, vi } from 'vitest';

const initialize = vi.fn();
const render = vi.fn();
const createRoot = vi.fn(() => ({ render }));

vi.mock('@azure/msal-browser', () => ({
  PublicClientApplication: vi.fn(() => ({ initialize })),
}));
vi.mock('react-dom/client', () => ({ default: { createRoot }, createRoot }));
vi.mock('./routes', () => ({ default: () => null }));
vi.mock('./hooks/useAuth', () => ({ MsalAuthProvider: ({ children }: { children: unknown }) => children }));

describe('application bootstrap', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
  });

  it('waits for the production MSAL adapter to initialize before rendering auth consumers', async () => {
    let resolveInitialization: () => void;
    initialize.mockReturnValueOnce(new Promise<void>((resolve) => { resolveInitialization = resolve; }));

    await import('./main');

    expect(initialize).toHaveBeenCalledOnce();
    expect(createRoot).not.toHaveBeenCalled();

    resolveInitialization!();
    await vi.waitFor(() => expect(render).toHaveBeenCalledOnce());
  });

  it('renders after an already-resolved MSAL initialization', async () => {
    initialize.mockResolvedValueOnce(undefined);

    await import('./main');

    await vi.waitFor(() => expect(render).toHaveBeenCalledOnce());
  });
});
