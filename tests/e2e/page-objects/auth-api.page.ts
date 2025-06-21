/**
 * Page Object Model for API Gateway Authentication API
 * Handles authentication-related API interactions for E2E tests
 */
import { expect, type APIRequestContext } from '@playwright/test';

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  username: string;
  is_admin: boolean;
}

export interface UserCredentials {
  username: string;
  password: string;
}

/**
 * AuthAPI page object for managing authentication flows
 */
export class AuthAPIPage {
  private request: APIRequestContext;
  private baseURL: string;

  constructor(request: APIRequestContext, baseURL: string = 'http://localhost:8000') {
    this.request = request;
    this.baseURL = baseURL;
  }

  /**
   * Login with username and password to get access token
   * @param credentials - User credentials
   * @returns Promise<AuthResponse> - Authentication response with token
   */
  async login(credentials: UserCredentials): Promise<AuthResponse> {
    const response = await this.request.post(`${this.baseURL}/api/v1/auth/token`, {
      form: {
        username: credentials.username,
        password: credentials.password,
        grant_type: 'password',
      },
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    expect(response.status()).toBe(200);
    const data = await response.json();

    // Validate response structure
    expect(data).toHaveProperty('access_token');
    expect(data).toHaveProperty('token_type', 'bearer');
    expect(data).toHaveProperty('expires_in');
    expect(data).toHaveProperty('user_id');
    expect(data).toHaveProperty('username', credentials.username);
    expect(data).toHaveProperty('is_admin');

    return data as AuthResponse;
  }

  /**
   * Attempt login with invalid credentials
   * @param credentials - Invalid user credentials
   */
  async loginWithInvalidCredentials(credentials: UserCredentials): Promise<void> {
    const response = await this.request.post(`${this.baseURL}/api/v1/auth/token`, {
      form: {
        username: credentials.username,
        password: credentials.password,
        grant_type: 'password',
      },
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    expect(response.status()).toBe(401);
    const data = await response.json();
    expect(data).toHaveProperty('detail', 'Incorrect username or password');
  }

  /**
   * Register a new user
   * @param userData - User registration data
   */
  async registerUser(userData: {
    username: string;
    email: string;
    password: string;
  }): Promise<void> {
    const response = await this.request.post(`${this.baseURL}/api/v1/auth/register`, {
      data: userData,
    });

    expect(response.status()).toBe(201);
    const data = await response.json();
    expect(data).toHaveProperty('message', 'User registered successfully');
    expect(data).toHaveProperty('username', userData.username);
  }

  /**
   * Access a protected endpoint with token
   * @param token - Access token
   * @param endpoint - Protected endpoint path
   * @returns Promise<any> - Response data
   */
  async accessProtectedEndpoint(
    token: string,
    endpoint: string = '/api/v1/user/profile'
  ): Promise<any> {
    const response = await this.request.get(`${this.baseURL}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return {
      status: response.status(),
      data: response.status() < 400 ? await response.json() : await response.text(),
    };
  }

  /**
   * Access protected endpoint without token
   * @param endpoint - Protected endpoint path
   */
  async accessProtectedEndpointWithoutToken(
    endpoint: string = '/api/v1/user/profile'
  ): Promise<void> {
    const response = await this.request.get(`${this.baseURL}${endpoint}`);

    // Should either succeed (no auth required) or return 401/403
    if (response.status() === 401 || response.status() === 403) {
      const data = await response.json();
      expect(data).toHaveProperty('detail');
    }
    // If it's 200, that means the endpoint doesn't require authentication
  }

  /**
   * Access protected endpoint with invalid token
   * @param invalidToken - Invalid token
   * @param endpoint - Protected endpoint path
   */
  async accessProtectedEndpointWithInvalidToken(
    invalidToken: string,
    endpoint: string = '/api/v1/user/profile'
  ): Promise<void> {
    const response = await this.request.get(`${this.baseURL}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${invalidToken}`,
      },
    });

    expect(response.status()).toBe(401);
    const data = await response.json();
    expect(data).toHaveProperty('detail');
  }

  /**
   * Check API health endpoint
   */
  async checkHealth(): Promise<void> {
    try {
      const response = await this.request.get(`${this.baseURL}/health`);
      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data).toHaveProperty('status', 'healthy');
    } catch (error) {
      throw new Error(`Health check failed: ${error.message}`);
    }
  }

  /**
   * Check if API server is available
   */
  async isServerAvailable(): Promise<boolean> {
    try {
      const response = await this.request.get(`${this.baseURL}/health`);
      return response.status() === 200;
    } catch (error) {
      return false;
    }
  }

  /**
   * Check API v1 health endpoint
   */
  async checkV1Health(): Promise<void> {
    const response = await this.request.get(`${this.baseURL}/api/v1/health`);
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
  }

  /**
   * Get API Gateway root information
   */
  async getApiInfo(): Promise<any> {
    const response = await this.request.get(`${this.baseURL}/`);
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('service');
    expect(data).toHaveProperty('version');
    expect(data).toHaveProperty('status', 'operational');

    return data;
  }

  /**
   * Create an expired or malformed token for testing
   * @param type - Type of invalid token to create
   */
  createInvalidToken(type: 'expired' | 'malformed' | 'empty'): string {
    switch (type) {
      case 'expired':
        // This is a JWT token that expired (you can create one with a past exp claim)
        return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTYwOTQ1OTIwMH0.invalid_signature';
      case 'malformed':
        return 'invalid.token.format';
      case 'empty':
        return '';
      default:
        return 'invalid_token';
    }
  }
}
