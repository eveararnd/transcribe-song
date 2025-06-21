/**
 * Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Layout from './Layout';
import { AuthProvider } from '../contexts/AuthContext';

// Mock useNavigate
const mockNavigate = vi.fn();
let mockPathname = '/';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ pathname: mockPathname })
  };
});

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {component}
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('Layout Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  test('renders layout with navigation', () => {
    renderWithProviders(<Layout />);

    expect(screen.getAllByText('Music Analyzer')[0]).toBeInTheDocument();
    // Check navigation items exist in the drawer
    const dashboardButton = screen.getAllByText('Dashboard')[0];
    const uploadButton = screen.getAllByText('Upload')[0];
    const searchButton = screen.getAllByText('Search')[0];
    
    expect(dashboardButton).toBeInTheDocument();
    expect(uploadButton).toBeInTheDocument();
    expect(searchButton).toBeInTheDocument();
  });

  test('shows login dialog when not authenticated', () => {
    renderWithProviders(<Layout />);

    expect(screen.getByText('Login to Music Analyzer')).toBeInTheDocument();
    expect(screen.getByLabelText('Username')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
  });

  test('handles login', async () => {
    renderWithProviders(<Layout />);

    const usernameInput = screen.getByLabelText('Username');
    const passwordInput = screen.getByLabelText('Password');
    const loginButton = screen.getByRole('button', { name: 'Login' });

    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'testpass' } });
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.queryByText('Login to Music Analyzer')).not.toBeInTheDocument();
    });
  });

  test('handles login with Enter key', async () => {
    renderWithProviders(<Layout />);

    const passwordInput = screen.getByLabelText('Password');
    
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'testpass' } });
    fireEvent.keyPress(passwordInput, { key: 'Enter', code: 'Enter', charCode: 13 });

    await waitFor(() => {
      expect(screen.queryByText('Login to Music Analyzer')).not.toBeInTheDocument();
    });
  });

  test('displays navigation menu items', () => {
    // Pre-authenticate
    sessionStorage.setItem('auth', JSON.stringify({ username: 'testuser', password: 'testpass' }));
    
    renderWithProviders(<Layout />);

    expect(screen.getAllByText('Dashboard')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Upload')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Search')[0]).toBeInTheDocument();
  });

  test('navigates when menu item clicked', () => {
    sessionStorage.setItem('auth', JSON.stringify({ username: 'testuser', password: 'testpass' }));
    
    renderWithProviders(<Layout />);

    fireEvent.click(screen.getAllByText('Upload')[0]);
    expect(mockNavigate).toHaveBeenCalledWith('/upload');
  });

  test('shows username when authenticated', () => {
    sessionStorage.setItem('auth', JSON.stringify({ username: 'testuser', password: 'testpass' }));
    
    renderWithProviders(<Layout />);

    expect(screen.getByText('testuser')).toBeInTheDocument();
  });

  test('handles logout', async () => {
    sessionStorage.setItem('auth', JSON.stringify({ username: 'testuser', password: 'testpass' }));
    
    renderWithProviders(<Layout />);

    const logoutButton = screen.getByTestId('LogoutIcon').closest('button');
    if (logoutButton) {
      fireEvent.click(logoutButton);
    }

    await waitFor(() => {
      expect(screen.getByText('Login to Music Analyzer')).toBeInTheDocument();
    });
  });

  test('mobile drawer toggle works', () => {
    sessionStorage.setItem('auth', JSON.stringify({ username: 'testuser', password: 'testpass' }));
    
    renderWithProviders(<Layout />);

    const menuButton = screen.getByLabelText('open drawer');
    fireEvent.click(menuButton);

    // Check if drawer items are visible
    const dashboardButtons = screen.getAllByText('Dashboard');
    expect(dashboardButtons.length).toBeGreaterThan(1); // One in drawer, one in main nav
  });

  test('highlights current route', () => {
    sessionStorage.setItem('auth', JSON.stringify({ username: 'testuser', password: 'testpass' }));
    
    // Set the pathname for this test
    mockPathname = '/upload';
    
    renderWithProviders(<Layout />);

    // The Upload menu item should be selected
    const uploadButtons = screen.getAllByText('Upload');
    // Check if any Upload button has the selected class
    const selectedButton = uploadButtons.find(btn => 
      btn.closest('[role="button"]')?.classList.contains('Mui-selected')
    );
    expect(selectedButton).toBeTruthy();
  });
});