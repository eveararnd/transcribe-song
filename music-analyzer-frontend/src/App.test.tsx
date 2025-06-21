/**
 * Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, test, expect, vi } from 'vitest';
import App from './App';

// Mock child components
vi.mock('./components/Layout', () => {
  return {
    default: function Layout() {
      const { Outlet } = require('react-router-dom');
      return <div data-testid="layout"><Outlet /></div>;
    }
  };
});

vi.mock('./pages/Dashboard', () => {
  return {
    default: function Dashboard() {
      return <div data-testid="dashboard">Dashboard</div>;
    }
  };
});

vi.mock('./pages/Upload', () => {
  return {
    default: function Upload() {
      return <div data-testid="upload">Upload</div>;
    }
  };
});

vi.mock('./pages/FileDetails', () => {
  return {
    default: function FileDetails() {
      return <div data-testid="file-details">File Details</div>;
    }
  };
});

vi.mock('./pages/SearchPage', () => {
  return {
    default: function SearchPage() {
      return <div data-testid="search">Search</div>;
    }
  };
});

describe('App Component', () => {
  test('renders without crashing', () => {
    render(<App />);
    expect(screen.getByTestId('layout')).toBeInTheDocument();
  });

  test('renders dashboard as default route', () => {
    render(<App />);
    expect(screen.getByTestId('dashboard')).toBeInTheDocument();
  });
});