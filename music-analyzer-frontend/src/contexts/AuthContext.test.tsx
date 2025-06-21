/**
 * Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
 */

import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { AuthProvider, useAuth } from './AuthContext';
import * as cookieUtils from '../utils/cookieUtils';

// Mock the cookie utils
vi.mock('../utils/cookieUtils', () => ({
  cookieUtils: {
    setAuthCookie: vi.fn(),
    getAuthCookie: vi.fn().mockReturnValue(null),
    removeAuthCookie: vi.fn(),
    getAuthHeaderFromCookie: vi.fn().mockReturnValue('')
  }
}));

// Test component that uses the auth context
const TestComponent: React.FC = () => {
  const { isAuthenticated, username, login, logout, getAuthHeader, isUsingCookie } = useAuth();
  
  return (
    <div>
      <div data-testid="is-authenticated">{isAuthenticated.toString()}</div>
      <div data-testid="username">{username || 'none'}</div>
      <div data-testid="auth-header">{getAuthHeader() || 'none'}</div>
      <div data-testid="is-using-cookie">{isUsingCookie.toString()}</div>
      <button onClick={() => login('testuser', 'testpass')}>Login</button>
      <button onClick={() => login('testuser', 'testpass', false)}>Login No Cookie</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    // Clear sessionStorage before each test
    sessionStorage.clear();
    // Reset all mocks
    vi.clearAllMocks();
  });

  test('provides authentication state', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
    expect(screen.getByTestId('username')).toHaveTextContent('none');
    expect(screen.getByTestId('auth-header')).toHaveTextContent('none');
  });

  test('login updates authentication state', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    act(() => {
      screen.getByText('Login').click();
    });

    expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true');
    expect(screen.getByTestId('username')).toHaveTextContent('testuser');
    expect(screen.getByTestId('auth-header')).toHaveTextContent('Basic ' + btoa('testuser:testpass'));
  });

  test('logout clears authentication state', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Login first
    act(() => {
      screen.getByText('Login').click();
    });

    // Then logout
    act(() => {
      screen.getByText('Logout').click();
    });

    expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
    expect(screen.getByTestId('username')).toHaveTextContent('none');
    expect(screen.getByTestId('auth-header')).toHaveTextContent('none');
    expect(cookieUtils.cookieUtils.removeAuthCookie).toHaveBeenCalled();
  });

  test('persists auth in sessionStorage and cookie', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    act(() => {
      screen.getByText('Login').click();
    });

    const storedAuth = sessionStorage.getItem('auth');
    expect(storedAuth).toBeTruthy();
    const parsed = JSON.parse(storedAuth!);
    expect(parsed.username).toBe('testuser');
    expect(parsed.password).toBe('testpass');
    expect(cookieUtils.cookieUtils.setAuthCookie).toHaveBeenCalledWith('testuser', 'testpass');
    expect(screen.getByTestId('is-using-cookie')).toHaveTextContent('true');
  });

  test('login without remember me does not set cookie', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    act(() => {
      screen.getByText('Login No Cookie').click();
    });

    expect(cookieUtils.cookieUtils.setAuthCookie).not.toHaveBeenCalled();
    expect(screen.getByTestId('is-using-cookie')).toHaveTextContent('false');
    const storedAuth = sessionStorage.getItem('auth');
    expect(storedAuth).toBeTruthy();
  });

  test('restores auth from sessionStorage on mount', () => {
    // Set auth in sessionStorage
    sessionStorage.setItem('auth', JSON.stringify({ username: 'saveduser', password: 'savedpass' }));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true');
    expect(screen.getByTestId('username')).toHaveTextContent('saveduser');
  });

  test('throws error when useAuth is used outside AuthProvider', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useAuth must be used within an AuthProvider');

    consoleSpy.mockRestore();
  });
});