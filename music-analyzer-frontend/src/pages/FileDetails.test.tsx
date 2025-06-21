/**
 * Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter } from 'react-router-dom';
import FileDetails from './FileDetails';
import api from '../services/api';

// Mock the API
vi.mock('../services/api');
const mockedApi = api as any;

// Mock useParams
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ fileId: 'test-file-id' })
  };
});

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { 
      retry: false,
      cacheTime: 0,
      staleTime: 0,
    },
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

describe('FileDetails Component', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = createTestQueryClient();
  });

  afterEach(() => {
    cleanup();
    queryClient.clear();
  });

  const mockFile = {
    id: 'test-file-id',
    filename: 'test_song.mp3',
    artist: 'Test Artist',
    title: 'Test Song',
    genre: 'rock',
    duration: 180.5,
    file_size: 5242880,
    transcribed: false,
    created_at: '2024-01-01T12:00:00Z'
  };

  const mockTranscriptions = [
    {
      id: 'trans-1',
      text: 'This is the transcribed text of the song',
      language: 'en',
      confidence: 0.95,
      created_at: '2024-01-01T12:05:00Z',
      word_timestamps: []
    }
  ];

  const mockLyrics = [
    {
      id: 'lyrics-1',
      source: 'genius',
      lyrics_text: 'These are the lyrics from Genius',
      confidence: 0.90,
      language: 'en',
      created_at: '2024-01-01T12:10:00Z'
    }
  ];

  test('displays loading state', async () => {
    mockedApi.getFile = vi.fn(() => new Promise(() => {}));
    mockedApi.getTranscriptions = vi.fn(() => new Promise(() => {}));
    mockedApi.getLyrics = vi.fn(() => new Promise(() => {}));
    
    renderWithProviders(<FileDetails />);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('displays error state', async () => {
    mockedApi.getFile = vi.fn().mockRejectedValueOnce(new Error('File not found'));
    mockedApi.getTranscriptions = vi.fn().mockResolvedValueOnce([]);
    mockedApi.getLyrics = vi.fn().mockResolvedValueOnce([]);
    
    renderWithProviders(<FileDetails />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load file details')).toBeInTheDocument();
    });
  });

  test('displays file information', async () => {
    mockedApi.getFile = vi.fn().mockResolvedValueOnce(mockFile);
    mockedApi.getTranscriptions = vi.fn().mockResolvedValueOnce([]);
    mockedApi.getLyrics = vi.fn().mockResolvedValueOnce([]);

    renderWithProviders(<FileDetails />);

    await waitFor(() => {
      expect(screen.getByText('test_song.mp3')).toBeInTheDocument();
      expect(screen.getByText('MP3')).toBeInTheDocument();
      expect(screen.getByText('3:00')).toBeInTheDocument();
      expect(screen.getByText('5 MB')).toBeInTheDocument();
      expect(screen.getByText('44100 Hz')).toBeInTheDocument();
      expect(screen.getByText('Stereo')).toBeInTheDocument();
      expect(screen.getByText('rock')).toBeInTheDocument();
    });
  });

  test('handles transcribe action', async () => {
    mockedApi.getFile = vi.fn().mockResolvedValueOnce(mockFile);
    mockedApi.getTranscriptions = vi.fn().mockResolvedValueOnce([]);
    mockedApi.getLyrics = vi.fn().mockResolvedValueOnce([]);
    mockedApi.transcribeFile = vi.fn().mockResolvedValueOnce(mockTranscriptions[0]);

    // Mock window.location.reload
    const reloadMock = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { reload: reloadMock },
      writable: true
    });

    renderWithProviders(<FileDetails />);

    await waitFor(() => {
      expect(screen.getByText('Transcribe Audio')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Transcribe Audio'));

    await waitFor(() => {
      expect(mockedApi.transcribeFile).toHaveBeenCalledWith({ file_id: 'test-file-id' });
      expect(reloadMock).toHaveBeenCalled();
    });
  });

  test('handles search lyrics action', async () => {
    mockedApi.getFile = vi.fn().mockResolvedValueOnce(mockFile);
    mockedApi.getTranscriptions = vi.fn().mockResolvedValueOnce([]);
    mockedApi.getLyrics = vi.fn().mockResolvedValueOnce([]);
    mockedApi.searchLyrics = vi.fn().mockResolvedValueOnce(mockLyrics);

    const reloadMock = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { reload: reloadMock },
      writable: true
    });

    renderWithProviders(<FileDetails />);

    await waitFor(() => {
      expect(screen.getByText('Search for Lyrics')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Search for Lyrics'));

    await waitFor(() => {
      expect(mockedApi.searchLyrics).toHaveBeenCalledWith('test-file-id');
      expect(reloadMock).toHaveBeenCalled();
    });
  });

  test('displays transcriptions', async () => {
    mockedApi.getFile = vi.fn().mockResolvedValueOnce(mockFile);
    mockedApi.getTranscriptions = vi.fn().mockResolvedValueOnce(mockTranscriptions);
    mockedApi.getLyrics = vi.fn().mockResolvedValueOnce([]);

    renderWithProviders(<FileDetails />);

    await waitFor(() => {
      expect(screen.getByText('This is the transcribed text of the song')).toBeInTheDocument();
      expect(screen.getByText('EN')).toBeInTheDocument();
      expect(screen.getByText('Confidence: 95.0%')).toBeInTheDocument();
    });
  });

  test('displays lyrics', async () => {
    mockedApi.getFile = vi.fn().mockResolvedValueOnce(mockFile);
    mockedApi.getTranscriptions = vi.fn().mockResolvedValueOnce([]);
    mockedApi.getLyrics = vi.fn().mockResolvedValueOnce(mockLyrics);

    renderWithProviders(<FileDetails />);

    // Switch to lyrics tab
    await waitFor(() => {
      fireEvent.click(screen.getByText('Lyrics (1)'));
    });

    expect(screen.getByText('These are the lyrics from Genius')).toBeInTheDocument();
    expect(screen.getByText('genius')).toBeInTheDocument();
    expect(screen.getByText('Confidence: 90.0%')).toBeInTheDocument();
  });

  test('displays metadata tab', async () => {
    mockedApi.getFile = vi.fn().mockResolvedValueOnce(mockFile);
    mockedApi.getTranscriptions = vi.fn().mockResolvedValueOnce([]);
    mockedApi.getLyrics = vi.fn().mockResolvedValueOnce([]);

    renderWithProviders(<FileDetails />);

    await waitFor(() => {
      fireEvent.click(screen.getByText('Metadata'));
    });

    expect(screen.getByText(/"artist": "Test Artist"/)).toBeInTheDocument();
    expect(screen.getByText(/"album": "Test Album"/)).toBeInTheDocument();
  });

  test('handles export menu', async () => {
    mockedApi.getFile = vi.fn().mockResolvedValueOnce(mockFile);
    mockedApi.getTranscriptions = vi.fn().mockResolvedValueOnce([]);
    mockedApi.getLyrics = vi.fn().mockResolvedValueOnce([]);

    renderWithProviders(<FileDetails />);

    await waitFor(() => {
      fireEvent.click(screen.getByText('Export'));
    });

    expect(screen.getByText('JSON')).toBeInTheDocument();
    expect(screen.getByText('CSV')).toBeInTheDocument();
    expect(screen.getByText('Excel')).toBeInTheDocument();
    expect(screen.getByText('ZIP')).toBeInTheDocument();
    expect(screen.getByText('TAR.GZ (Original)')).toBeInTheDocument();
    expect(screen.getByText('TAR.GZ (Mono)')).toBeInTheDocument();
  });

  test('handles export action', async () => {
    mockedApi.getFile = vi.fn().mockResolvedValueOnce(mockFile);
    mockedApi.getTranscriptions = vi.fn().mockResolvedValueOnce([]);
    mockedApi.getLyrics = vi.fn().mockResolvedValueOnce([]);
    
    const mockBlob = new Blob(['export data']);
    mockedApi.exportFile = vi.fn().mockResolvedValueOnce(mockBlob);

    // Mock URL and document methods
    global.URL = global.URL || {};
    global.URL.createObjectURL = vi.fn(() => 'blob:test');
    global.URL.revokeObjectURL = vi.fn();
    
    // Track anchor element creation
    let anchorElement: HTMLAnchorElement | null = null;
    const originalCreateElement = document.createElement.bind(document);
    vi.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
      const element = originalCreateElement(tagName);
      if (tagName === 'a') {
        anchorElement = element as HTMLAnchorElement;
        // Override click to prevent navigation
        element.click = vi.fn();
      }
      return element;
    });

    renderWithProviders(<FileDetails />);

    await waitFor(() => {
      fireEvent.click(screen.getByText('Export'));
    });

    fireEvent.click(screen.getByText('JSON'));

    await waitFor(() => {
      expect(mockedApi.exportFile).toHaveBeenCalledWith('test-file-id', 'json');
      expect(anchorElement).not.toBeNull();
      expect(anchorElement?.download).toBe('test_song.mp3.json');
      expect(anchorElement?.click).toHaveBeenCalled();
    });
  });

  test('shows empty state for transcriptions', async () => {
    mockedApi.getFile = vi.fn().mockResolvedValueOnce(mockFile);
    mockedApi.getTranscriptions = vi.fn().mockResolvedValueOnce([]);
    mockedApi.getLyrics = vi.fn().mockResolvedValueOnce([]);

    renderWithProviders(<FileDetails />);

    await waitFor(() => {
      expect(screen.getByText(/No transcriptions yet/)).toBeInTheDocument();
    });
  });

  test('shows empty state for lyrics', async () => {
    mockedApi.getFile = vi.fn().mockResolvedValueOnce(mockFile);
    mockedApi.getTranscriptions = vi.fn().mockResolvedValueOnce([]);
    mockedApi.getLyrics = vi.fn().mockResolvedValueOnce([]);

    renderWithProviders(<FileDetails />);

    await waitFor(() => {
      fireEvent.click(screen.getByText('Lyrics (0)'));
    });

    expect(screen.getByText(/No lyrics found yet/)).toBeInTheDocument();
  });

  test('handles mono channel display', async () => {
    const monoFile = { ...mockFile, channels: 1 };
    mockedApi.getFile = vi.fn().mockResolvedValueOnce(monoFile);
    mockedApi.getTranscriptions = vi.fn().mockResolvedValueOnce([]);
    mockedApi.getLyrics = vi.fn().mockResolvedValueOnce([]);

    renderWithProviders(<FileDetails />);

    await waitFor(() => {
      expect(screen.getByText('Mono')).toBeInTheDocument();
    });
  });

  test('handles multi-channel display', async () => {
    const multiChannelFile = { ...mockFile, channels: 5 };
    mockedApi.getFile = vi.fn().mockResolvedValueOnce(multiChannelFile);
    mockedApi.getTranscriptions = vi.fn().mockResolvedValueOnce([]);
    mockedApi.getLyrics = vi.fn().mockResolvedValueOnce([]);

    renderWithProviders(<FileDetails />);

    await waitFor(() => {
      expect(screen.getByText('5 channels')).toBeInTheDocument();
    });
  });

  test('handles missing genre', async () => {
    const fileWithoutGenre = { ...mockFile, genre: undefined };
    mockedApi.getFile = vi.fn().mockResolvedValueOnce(fileWithoutGenre);
    mockedApi.getTranscriptions = vi.fn().mockResolvedValueOnce([]);
    mockedApi.getLyrics = vi.fn().mockResolvedValueOnce([]);

    renderWithProviders(<FileDetails />);

    await waitFor(() => {
      expect(screen.getByText('Unknown')).toBeInTheDocument();
    });
  });
});