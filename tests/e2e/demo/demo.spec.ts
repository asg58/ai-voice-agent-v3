/**
 * Demo E2E Test to verify testing framework setup
 *
 * This test demonstrates the Playwright testing framework is working correctly
 * without requiring the API Gateway server to be running.
 *
 * @group demo
 */
import { test, expect } from '@playwright/test';

test.describe('Playwright Framework Demo', () => {
  test('should verify testing framework is working', async () => {
    // Assert: Basic framework functionality
    expect(1 + 1).toBe(2);
    expect('hello world').toContain('world');
    expect([1, 2, 3]).toHaveLength(3);
  });

  test('should verify API request capabilities', async ({ request }) => {
    // Test making HTTP requests (using a public API)
    const response = await request.get('https://httpbin.org/status/200');
    expect(response.status()).toBe(200);
  });

  test('should verify JSON API response handling', async ({ request }) => {
    // Test JSON response handling
    const response = await request.get('https://httpbin.org/json');
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('slideshow');
  });

  test('should verify POST request capabilities', async ({ request }) => {
    // Test POST request
    const testData = {
      username: 'test_user',
      action: 'demo_test',
    };

    const response = await request.post('https://httpbin.org/post', {
      data: testData,
    });

    expect(response.status()).toBe(200);
    const responseData = await response.json();
    expect(responseData.json).toEqual(testData);
  });

  test('should verify authentication header handling', async ({ request }) => {
    // Test authentication headers
    const response = await request.get('https://httpbin.org/bearer', {
      headers: {
        Authorization: 'Bearer demo_token_12345',
      },
    });

    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('authenticated', true);
    expect(data).toHaveProperty('token', 'demo_token_12345');
  });

  test('should demonstrate error handling for 401 responses', async ({ request }) => {
    // Test 401 Unauthorized response
    const response = await request.get('https://httpbin.org/status/401');
    expect(response.status()).toBe(401);
  });

  test('should demonstrate concurrent API requests', async ({ request }) => {
    // Test multiple concurrent requests
    const requests = [
      request.get('https://httpbin.org/delay/1'),
      request.get('https://httpbin.org/status/200'),
      request.get('https://httpbin.org/json'),
    ];

    const responses = await Promise.all(requests);

    // All requests should complete
    expect(responses).toHaveLength(3);
    responses.forEach((response) => {
      expect(response.status()).toBe(200);
    });
  });
});
