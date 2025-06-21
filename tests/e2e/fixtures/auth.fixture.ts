/**
 * Authentication fixtures for E2E tests
 * Provides reusable authentication setup and teardown functionality
 */
import { test as base, expect } from '@playwright/test';
import {
  AuthAPIPage,
  type AuthResponse,
  type UserCredentials,
} from '../page-objects/auth-api.page';

// Define test user credentials
export const TEST_USERS = {
  admin: {
    username: 'admin',
    password: 'password',
  },
  user: {
    username: 'user',
    password: 'password',
  },
  invalid: {
    username: 'nonexistent',
    password: 'wrongpassword',
  },
} as const;

// Extended test context with authentication fixtures
type AuthFixtures = {
  authAPI: AuthAPIPage;
  adminToken: string;
  userToken: string;
  authenticatedAsAdmin: AuthResponse;
  authenticatedAsUser: AuthResponse;
};

/**
 * Extended Playwright test with authentication fixtures
 */
export const test = base.extend<AuthFixtures>({
  /**
   * AuthAPI page object fixture
   */
  authAPI: async ({ request, baseURL }, use) => {
    const authAPI = new AuthAPIPage(request, baseURL);

    // Try to verify API is healthy before running tests, but don't fail if it's not available
    try {
      await authAPI.checkHealth();
    } catch (error) {
      console.warn('⚠️ API server not available, some tests may be skipped:', error.message);
    }

    await use(authAPI);
  },

  /**
   * Admin access token fixture
   * Provides a valid admin token for tests that need admin privileges
   */
  adminToken: async ({ authAPI }, use) => {
    const authResponse = await authAPI.login(TEST_USERS.admin);
    await use(authResponse.access_token);
  },

  /**
   * Regular user access token fixture
   * Provides a valid user token for tests that need basic authentication
   */
  userToken: async ({ authAPI }, use) => {
    const authResponse = await authAPI.login(TEST_USERS.user);
    await use(authResponse.access_token);
  },

  /**
   * Full admin authentication fixture
   * Provides complete admin authentication response for detailed testing
   */
  authenticatedAsAdmin: async ({ authAPI }, use) => {
    const authResponse = await authAPI.login(TEST_USERS.admin);

    // Validate admin privileges
    expect(authResponse.is_admin).toBe(true);
    expect(authResponse.username).toBe(TEST_USERS.admin.username);

    await use(authResponse);
  },

  /**
   * Full user authentication fixture
   * Provides complete user authentication response for detailed testing
   */
  authenticatedAsUser: async ({ authAPI }, use) => {
    const authResponse = await authAPI.login(TEST_USERS.user);

    // Validate user privileges
    expect(authResponse.is_admin).toBe(false);
    expect(authResponse.username).toBe(TEST_USERS.user.username);

    await use(authResponse);
  },
});

/**
 * Custom expect matcher for authentication responses
 */
export function expectValidAuthResponse(response: AuthResponse, expectedUsername: string) {
  expect(response).toMatchObject({
    access_token: expect.any(String),
    token_type: 'bearer',
    expires_in: expect.any(Number),
    user_id: expect.any(String),
    username: expectedUsername,
    is_admin: expect.any(Boolean),
  });

  // Token should be a valid JWT (3 parts separated by dots)
  expect(response.access_token.split('.')).toHaveLength(3);

  // Expires in should be positive
  expect(response.expires_in).toBeGreaterThan(0);
}

export { expect } from '@playwright/test';
