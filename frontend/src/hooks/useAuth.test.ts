import { renderHook, act } from '../test-utils';
import { useAuth } from './useAuth';

describe('useAuth', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  it('should initialize with loading false and user null after effect runs', () => {
    const { result } = renderHook(() => useAuth());
    
    // useEffect runs synchronously in test environment, setting loading to false
    expect(result.current.loading).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('should return true for hasRole only if user has the specified role', () => {
    const { result } = renderHook(() => useAuth());
    const mockUser = { email: 'test@example.com', fullName: 'Test User', roles: ['Admin'] as const };
    const mockToken = 'fake-jwt-token';

    act(() => {
      result.current.login(mockUser, mockToken);
    });

    expect(result.current.hasRole('Admin')).toBe(true);
    expect(result.current.hasRole('Viewer')).toBe(false);
  });

  it('should login and set user and token in localStorage', () => {
    const { result } = renderHook(() => useAuth());
    
    const mockUser = { email: 'test@example.com', fullName: 'Test User', roles: ['Viewer'] as const };
    const mockToken = 'fake-jwt-token';

    act(() => {
      result.current.login(mockUser, mockToken);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(localStorage.getItem('auth_token')).toBe(mockToken);
    expect(localStorage.getItem('user_profile')).toBe(JSON.stringify(mockUser));
  });

  it('should return false for hasRole if user has no roles', () => {
    const { result } = renderHook(() => useAuth());
    
    // Initially user is null, so hasRole should be false
    expect(result.current.hasRole('Admin')).toBe(false);
  });

  it('should hydrate user and token from localStorage on mount', () => {
    const mockUser = { email: 'test@example.com', fullName: 'Test User', roles: ['Admin'] as const };
    const mockToken = 'fake-jwt-token';

    localStorage.setItem('auth_token', mockToken);
    localStorage.setItem('user_profile', JSON.stringify(mockUser));

    const { result } = renderHook(() => useAuth());

    expect(result.current.user).toEqual(mockUser);
  });

  it('should clear user and token from state and localStorage on logout', () => {
    const { result } = renderHook(() => useAuth());
    const mockUser = { email: 'test@example.com', fullName: 'Test User', roles: ['Admin'] as const };
    const mockToken = 'fake-jwt-token';

    act(() => {
      result.current.login(mockUser, mockToken);
    });

    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(localStorage.getItem('auth_token')).toBeNull();
    expect(localStorage.getItem('user_profile')).toBeNull();
  });
});
