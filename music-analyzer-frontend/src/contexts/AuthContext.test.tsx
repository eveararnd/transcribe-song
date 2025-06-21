/**
 * Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
 */

import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { AuthProvider, useAuth } from './AuthContext';

// Test component that uses the auth context
const TestComponent: React.FC = () => {
  const { isAuthenticated, username, login, logout, getAuthHeader } = useAuth();
  
  return (
    <div>
      <div data-testid="is-authenticated">{isAuthenticated.toString()}</div>
      <div data-testid="username">{username || 'none'}</div>
      <div data-testid="auth-header">{getAuthHeader() || 'none'}</div>
      <button onClick={() => login('testuser', 'testpass')}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    // Clear sessionStorage before each test
    sessionStorage.clear();
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
  });

  test('persists auth in sessionStorage', () => {
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