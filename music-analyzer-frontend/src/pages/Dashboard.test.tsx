/**
 * Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from './Dashboard';
import api from '../services/api';

// Mock the API
vi.mock('../services/api');
const mockedApi = api as any;

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate
  };
});

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockFiles = [
    {
      id: '1',
      original_filename: 'song1.mp3',
      file_format: 'mp3',
      duration: 180,
      file_size: 5242880,
      genre: 'rock',
      uploaded_at: '2024-01-01T12:00:00Z',
      sample_rate: 44100,
      channels: 2,
      bit_depth: 16,
      metadata: {}
    },
    {
      id: '2',
      original_filename: 'song2.flac',
      file_format: 'flac',
      duration: 240,
      file_size: 10485760,
      genre: 'jazz',
      uploaded_at: '2024-01-02T12:00:00Z',
      sample_rate: 48000,
      channels: 2,
      bit_depth: 24,
      metadata: {}
    }
  ];

  const mockStats = {
    total_files: 10,
    total_size: 104857600,
    by_format: {
      mp3: { count: 6, size: 62914560 },
      flac: { count: 4, size: 41943040 }
    },
    by_genre: {
      rock: { count: 5, size: 52428800 },
      jazz: { count: 5, size: 52428800 }
    }
  };

  test('displays loading state', () => {
    mockedApi.getFiles = vi.fn(() => new Promise(() => {}));
    mockedApi.getStorageStats = vi.fn(() => new Promise(() => {}));

    renderWithProviders(<Dashboard />);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('displays error state', async () => {
    mockedApi.getFiles = vi.fn().mockRejectedValueOnce(new Error('API Error'));
    mockedApi.getStorageStats = vi.fn().mockResolvedValueOnce(mockStats);

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Error loading files/)).toBeInTheDocument();
    });
  });

  test('displays statistics cards', async () => {
    mockedApi.getFiles = vi.fn().mockResolvedValueOnce(mockFiles);
    mockedApi.getStorageStats = vi.fn().mockResolvedValueOnce(mockStats);

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Total Files')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('Total Size')).toBeInTheDocument();
      expect(screen.getByText('100 MB')).toBeInTheDocument();
      expect(screen.getByText('File Formats')).toBeInTheDocument();
      expect(screen.getAllByText('2')[0]).toBeInTheDocument();
      expect(screen.getByText('Genres')).toBeInTheDocument();
    });
  });

  test('displays files table', async () => {
    mockedApi.getFiles = vi.fn().mockResolvedValueOnce(mockFiles);
    mockedApi.getStorageStats = vi.fn().mockResolvedValueOnce(mockStats);

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Recent Files')).toBeInTheDocument();
      expect(screen.getByText('song1.mp3')).toBeInTheDocument();
      expect(screen.getByText('song2.flac')).toBeInTheDocument();
      expect(screen.getByText('MP3')).toBeInTheDocument();
      expect(screen.getByText('FLAC')).toBeInTheDocument();
      expect(screen.getByText('3:00')).toBeInTheDocument(); // 180 seconds
      expect(screen.getByText('4:00')).toBeInTheDocument(); // 240 seconds
      expect(screen.getByText('5 MB')).toBeInTheDocument();
      expect(screen.getByText('10 MB')).toBeInTheDocument();
    });
  });

  test('navigates to file details on view button click', async () => {
    mockedApi.getFiles = vi.fn().mockResolvedValueOnce(mockFiles);
    mockedApi.getStorageStats = vi.fn().mockResolvedValueOnce(mockStats);

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      const viewButtons = screen.getAllByTitle('View Details');
      fireEvent.click(viewButtons[0]);
    });

    expect(mockNavigate).toHaveBeenCalledWith('/file/1');
  });

  test('downloads file on download button click', async () => {
    mockedApi.getFiles = vi.fn().mockResolvedValueOnce(mockFiles);
    mockedApi.getStorageStats = vi.fn().mockResolvedValueOnce(mockStats);
    
    const mockBlob = new Blob(['test data']);
    mockedApi.exportFile = vi.fn().mockResolvedValueOnce(mockBlob);

    // Mock URL and anchor element behavior
    global.URL = global.URL || {};
    global.URL.createObjectURL = vi.fn(() => 'blob:test');
    global.URL.revokeObjectURL = vi.fn();
    
    // Track anchor element creation and click
    let anchorElement: HTMLAnchorElement | null = null;
    const originalCreateElement = document.createElement.bind(document);
    const createElementSpy = vi.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
      const element = originalCreateElement(tagName);
      if (tagName === 'a') {
        anchorElement = element as HTMLAnchorElement;
        // Override click to prevent navigation
        element.click = vi.fn(() => {
          // Don't actually navigate
        });
      }
      return element;
    });

    renderWithProviders(<Dashboard />);

    // Wait for the table to load
    await waitFor(() => {
      expect(screen.getByText('song1.mp3')).toBeInTheDocument();
    });

    const downloadButtons = screen.getAllByTitle('Download');
    fireEvent.click(downloadButtons[0]);

    await waitFor(() => {
      expect(mockedApi.exportFile).toHaveBeenCalledWith('1', 'json');
      expect(global.URL.createObjectURL).toHaveBeenCalled();
      expect(anchorElement).not.toBeNull();
      expect(anchorElement?.download).toBe('song1.mp3.json');
      expect(anchorElement?.click).toHaveBeenCalled();
      expect(global.URL.revokeObjectURL).toHaveBeenCalled();
    });

    // Cleanup
    createElementSpy.mockRestore();
  });

  test('displays empty state when no files', async () => {
    mockedApi.getFiles = vi.fn().mockResolvedValueOnce([]);
    mockedApi.getStorageStats = vi.fn().mockResolvedValueOnce({
      total_files: 0,
      total_size: 0,
      by_format: {},
      by_genre: {}
    });

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('No files uploaded yet. Start by uploading a music file.')).toBeInTheDocument();
    });
  });

  test('formats file information correctly', async () => {
    mockedApi.getFiles = vi.fn().mockResolvedValueOnce(mockFiles);
    mockedApi.getStorageStats = vi.fn().mockResolvedValueOnce(mockStats);

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      // Check date formatting
      expect(screen.getByText('Jan 01, 2024')).toBeInTheDocument();
      expect(screen.getByText('Jan 02, 2024')).toBeInTheDocument();
      
      // Check genre display
      expect(screen.getByText('rock')).toBeInTheDocument();
      expect(screen.getByText('jazz')).toBeInTheDocument();
    });
  });

  test('handles missing genre gracefully', async () => {
    const filesWithoutGenre = [{
      ...mockFiles[0],
      genre: undefined
    }];
    
    mockedApi.getFiles = vi.fn().mockResolvedValueOnce(filesWithoutGenre);
    mockedApi.getStorageStats = vi.fn().mockResolvedValueOnce(mockStats);

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('-')).toBeInTheDocument();
    });
  });
});