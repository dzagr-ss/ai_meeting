import authReducer, {
  loginStart,
  loginSuccess,
  loginFailure,
  logout,
  validateToken,
} from '../authSlice';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('authSlice', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  const initialState = {
    token: null,
    user: null,
    isAuthenticated: false,
    loading: false,
    error: null,
  };

  describe('initial state', () => {
    it('should have correct initial state when no token in localStorage', () => {
      const state = authReducer(undefined, { type: 'unknown' });
      expect(state).toEqual(initialState);
    });

    it('should initialize with valid token from localStorage', () => {
      // Create a valid JWT token (expires in 1 hour)
      const exp = Math.floor(Date.now() / 1000) + 3600;
      const payload = { sub: 'test@example.com', user_type: 'normal', exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;
      
      localStorageMock.getItem.mockReturnValue(mockToken);
      
      // Re-import to trigger initialization with mocked localStorage
      jest.resetModules();
      const { default: freshAuthReducer } = require('../authSlice');
      
      const state = freshAuthReducer(undefined, { type: 'unknown' });
      expect(state.isAuthenticated).toBe(true);
      expect(state.token).toBe(mockToken);
      expect(state.user?.email).toBe('test@example.com');
    });

    it('should clear expired token from localStorage on initialization', () => {
      // Create an expired JWT token
      const exp = Math.floor(Date.now() / 1000) - 3600; // 1 hour ago
      const payload = { sub: 'test@example.com', user_type: 'normal', exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const expiredToken = `header.${encodedPayload}.signature`;
      
      localStorageMock.getItem.mockReturnValue(expiredToken);
      
      jest.resetModules();
      require('../authSlice');
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');
    });
  });

  describe('loginStart', () => {
    it('should set loading to true and clear error', () => {
      const state = authReducer(
        { ...initialState, error: 'Previous error' },
        loginStart()
      );
      
      expect(state.loading).toBe(true);
      expect(state.error).toBe(null);
    });
  });

  describe('loginSuccess', () => {
    it('should set authentication state and store token', () => {
      const exp = Math.floor(Date.now() / 1000) + 3600;
      const payload = { sub: 'test@example.com', user_type: 'admin', exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const token = `header.${encodedPayload}.signature`;

      const state = authReducer(
        { ...initialState, loading: true },
        loginSuccess(token)
      );

      expect(state.loading).toBe(false);
      expect(state.isAuthenticated).toBe(true);
      expect(state.token).toBe(token);
      expect(state.user?.email).toBe('test@example.com');
      expect(state.user?.user_type).toBe('admin');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('token', token);
    });

    it('should handle malformed token gracefully', () => {
      const malformedToken = 'invalid.token.here';

      const state = authReducer(
        { ...initialState, loading: true },
        loginSuccess(malformedToken)
      );

      expect(state.loading).toBe(false);
      expect(state.isAuthenticated).toBe(true);
      expect(state.token).toBe(malformedToken);
      expect(state.user).toBe(null); // Should be null for malformed token
    });
  });

  describe('loginFailure', () => {
    it('should set error message and stop loading', () => {
      const errorMessage = 'Invalid credentials';
      
      const state = authReducer(
        { ...initialState, loading: true },
        loginFailure(errorMessage)
      );

      expect(state.loading).toBe(false);
      expect(state.error).toBe(errorMessage);
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('logout', () => {
    it('should clear all authentication state', () => {
      const authenticatedState = {
        token: 'some-token',
        user: { email: 'test@example.com', user_type: 'normal' },
        isAuthenticated: true,
        loading: false,
        error: null,
      };

      const state = authReducer(authenticatedState, logout());

      expect(state.token).toBe(null);
      expect(state.user).toBe(null);
      expect(state.isAuthenticated).toBe(false);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');
    });
  });

  describe('validateToken', () => {
    it('should do nothing with valid token', () => {
      const exp = Math.floor(Date.now() / 1000) + 3600; // 1 hour from now
      const payload = { sub: 'test@example.com', user_type: 'normal', exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const validToken = `header.${encodedPayload}.signature`;

      const authenticatedState = {
        token: validToken,
        user: { email: 'test@example.com', user_type: 'normal', exp },
        isAuthenticated: true,
        loading: false,
        error: null,
      };

      const state = authReducer(authenticatedState, validateToken());

      expect(state.isAuthenticated).toBe(true);
      expect(state.token).toBe(validToken);
      expect(localStorageMock.removeItem).not.toHaveBeenCalled();
    });

    it('should clear expired token', () => {
      const exp = Math.floor(Date.now() / 1000) - 3600; // 1 hour ago
      const payload = { sub: 'test@example.com', user_type: 'normal', exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const expiredToken = `header.${encodedPayload}.signature`;

      const authenticatedState = {
        token: expiredToken,
        user: { email: 'test@example.com', user_type: 'normal', exp },
        isAuthenticated: true,
        loading: false,
        error: null,
      };

      const state = authReducer(authenticatedState, validateToken());

      expect(state.token).toBe(null);
      expect(state.user).toBe(null);
      expect(state.isAuthenticated).toBe(false);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');
    });

    it('should clear malformed token', () => {
      const malformedToken = 'invalid.token';

      const authenticatedState = {
        token: malformedToken,
        user: { email: 'test@example.com', user_type: 'normal' },
        isAuthenticated: true,
        loading: false,
        error: null,
      };

      const state = authReducer(authenticatedState, validateToken());

      expect(state.token).toBe(null);
      expect(state.user).toBe(null);
      expect(state.isAuthenticated).toBe(false);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');
    });

    it('should handle state with no token', () => {
      const state = authReducer(initialState, validateToken());
      
      expect(state).toEqual(initialState);
      expect(localStorageMock.removeItem).not.toHaveBeenCalled();
    });
  });

  describe('edge cases', () => {
    it('should handle token with missing payload', () => {
      const tokenWithoutPayload = 'header..signature';
      
      const state = authReducer(
        initialState,
        loginSuccess(tokenWithoutPayload)
      );
      
      expect(state.user).toBe(null);
      expect(state.isAuthenticated).toBe(true);
      expect(state.token).toBe(tokenWithoutPayload);
    });

    it('should handle token with invalid JSON payload', () => {
      const invalidJsonPayload = btoa('invalid json');
      const invalidToken = `header.${invalidJsonPayload}.signature`;
      
      const state = authReducer(
        initialState,
        loginSuccess(invalidToken)
      );
      
      expect(state.user).toBe(null);
      expect(state.isAuthenticated).toBe(true);
    });
  });
}); 