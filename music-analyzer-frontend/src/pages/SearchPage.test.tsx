/**
 * Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import SearchPage from './SearchPage';
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

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('SearchPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockSearchResults = [
    {
      file: {
        id: '1',
        filename: 'result1.mp3',
        artist: 'Artist 1',
        title: 'Result Song 1',
        genre: 'rock',
        duration: 180,
        file_size: 5242880,
        transcribed: true,
        created_at: '2024-01-01T12:00:00Z'
      },
      transcriptions: [{
        id: 'trans-1',
        text: 'This is the transcription that matches the search query',
        language: 'en',
        confidence: 0.95,
        created_at: '2024-01-01T12:05:00Z',
        word_timestamps: []
      }],
      lyrics: [{
        id: 'lyrics-1',
        source: 'genius',
        lyrics_text: 'Matching lyrics text here',
        confidence: 0.90,
        language: 'en',
        created_at: '2024-01-01T12:10:00Z'
      }],
      similarity_score: 0.85
    }
  ];

  test('renders search interface', () => {
    renderWithRouter(<SearchPage />);

    expect(screen.getByText('Search Music')).toBeInTheDocument();
    expect(screen.getByText('Similar Content')).toBeInTheDocument();
    expect(screen.getByText('Search by Lyrics')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter text to find similar music...')).toBeInTheDocument();
  });

  test('switches search modes', () => {
    renderWithRouter(<SearchPage />);

    const lyricsButton = screen.getByText('Search by Lyrics');
    fireEvent.click(lyricsButton);

    expect(screen.getByPlaceholderText('Enter lyrics to search...')).toBeInTheDocument();
  });

  test('handles similar content search', async () => {
    mockedApi.searchSimilar = vi.fn().mockResolvedValueOnce(mockSearchResults);

    renderWithRouter(<SearchPage />);

    const searchInput = screen.getByPlaceholderText('Enter text to find similar music...');
    const searchButton = screen.getByText('Search');

    fireEvent.change(searchInput, { target: { value: 'test query' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(mockedApi.searchSimilar).toHaveBeenCalledWith('test query');
      expect(screen.getByText('Found 1 results')).toBeInTheDocument();
      expect(screen.getByText('result1.mp3')).toBeInTheDocument();
      expect(screen.getByText('85.0% match')).toBeInTheDocument();
    });
  });

  test('handles lyrics search', async () => {
    mockedApi.searchByLyrics = vi.fn().mockResolvedValueOnce(mockSearchResults);

    renderWithRouter(<SearchPage />);

    // Switch to lyrics mode
    fireEvent.click(screen.getByText('Search by Lyrics'));

    const searchInput = screen.getByPlaceholderText('Enter lyrics to search...');
    const searchButton = screen.getByText('Search');

    fireEvent.change(searchInput, { target: { value: 'lyrics query' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(mockedApi.searchByLyrics).toHaveBeenCalledWith('lyrics query');
      expect(screen.getByText('Found 1 results')).toBeInTheDocument();
    });
  });

  test('handles search with Enter key', async () => {
    mockedApi.searchSimilar = vi.fn().mockResolvedValueOnce([]);

    renderWithRouter(<SearchPage />);

    const searchInput = screen.getByPlaceholderText('Enter text to find similar music...');
    
    fireEvent.change(searchInput, { target: { value: 'test query' } });
    fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter', charCode: 13 });

    await waitFor(() => {
      expect(mockedApi.searchSimilar).toHaveBeenCalledWith('test query');
    });
  });

  test('displays search results with details', async () => {
    mockedApi.searchSimilar = vi.fn().mockResolvedValueOnce(mockSearchResults);

    renderWithRouter(<SearchPage />);

    const searchInput = screen.getByPlaceholderText('Enter text to find similar music...');
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.click(screen.getByText('Search'));

    await waitFor(() => {
      expect(screen.getByText('MP3')).toBeInTheDocument();
      expect(screen.getByText('3:00')).toBeInTheDocument();
      expect(screen.getByText('rock')).toBeInTheDocument();
      expect(screen.getByText(/This is the transcription/)).toBeInTheDocument();
      expect(screen.getByText(/Matching lyrics text/)).toBeInTheDocument();
      expect(screen.getByText(/genius/i)).toBeInTheDocument();
    });
  });

  test('navigates to file details on view button click', async () => {
    mockedApi.searchSimilar = vi.fn().mockResolvedValueOnce(mockSearchResults);

    renderWithRouter(<SearchPage />);

    const searchInput = screen.getByPlaceholderText('Enter text to find similar music...');
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.click(screen.getByText('Search'));

    await waitFor(() => {
      fireEvent.click(screen.getByText('View Details'));
    });

    expect(mockNavigate).toHaveBeenCalledWith('/file/1');
  });

  test('shows loading state during search', async () => {
    mockedApi.searchSimilar = vi.fn().mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve([]), 100))
    );

    renderWithRouter(<SearchPage />);

    const searchInput = screen.getByPlaceholderText('Enter text to find similar music...');
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.click(screen.getByText('Search'));

    expect(screen.getByText('Searching...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('handles search error', async () => {
    mockedApi.searchSimilar = vi.fn().mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Search service unavailable'
        }
      }
    });

    renderWithRouter(<SearchPage />);

    const searchInput = screen.getByPlaceholderText('Enter text to find similar music...');
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.click(screen.getByText('Search'));

    await waitFor(() => {
      expect(screen.getByText('Search service unavailable')).toBeInTheDocument();
    });
  });

  test('shows no results message', async () => {
    mockedApi.searchSimilar = vi.fn().mockResolvedValueOnce([]);

    renderWithRouter(<SearchPage />);

    const searchInput = screen.getByPlaceholderText('Enter text to find similar music...');
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
    fireEvent.click(screen.getByText('Search'));

    await waitFor(() => {
      expect(screen.getByText('No results found. Try a different search query.')).toBeInTheDocument();
    });
  });

  test('prevents search with empty query', () => {
    renderWithRouter(<SearchPage />);

    const searchButton = screen.getByText('Search');
    
    expect(searchButton).toBeDisabled();
  });

  test('enables search button when query is entered', () => {
    renderWithRouter(<SearchPage />);

    const searchInput = screen.getByPlaceholderText('Enter text to find similar music...');
    const searchButton = screen.getByText('Search');
    
    fireEvent.change(searchInput, { target: { value: 'test' } });
    
    expect(searchButton).not.toBeDisabled();
  });

  test('clears previous results on new search', async () => {
    mockedApi.searchSimilar = vi.fn()
      .mockResolvedValueOnce(mockSearchResults)
      .mockResolvedValueOnce([]);

    renderWithRouter(<SearchPage />);

    // First search
    const searchInput = screen.getByPlaceholderText('Enter text to find similar music...');
    fireEvent.change(searchInput, { target: { value: 'first query' } });
    fireEvent.click(screen.getByText('Search'));

    await waitFor(() => {
      expect(screen.getByText('Found 1 results')).toBeInTheDocument();
    });

    // Second search
    fireEvent.change(searchInput, { target: { value: 'second query' } });
    fireEvent.click(screen.getByText('Search'));

    await waitFor(() => {
      expect(screen.queryByText('Found 1 results')).not.toBeInTheDocument();
      expect(screen.getByText('No results found. Try a different search query.')).toBeInTheDocument();
    });
  });

  test('formats duration correctly', async () => {
    const resultWithLongDuration = [{
      ...mockSearchResults[0],
      file: {
        ...mockSearchResults[0].file,
        duration: 3661 // 1 hour, 1 minute, 1 second
      }
    }];

    mockedApi.searchSimilar = vi.fn().mockResolvedValueOnce(resultWithLongDuration);

    renderWithRouter(<SearchPage />);

    const searchInput = screen.getByPlaceholderText('Enter text to find similar music...');
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.click(screen.getByText('Search'));

    await waitFor(() => {
      expect(screen.getByText('61:01')).toBeInTheDocument();
    });
  });

  test('handles results without transcriptions', async () => {
    const resultsNoTranscriptions = [{
      ...mockSearchResults[0],
      transcriptions: []
    }];

    mockedApi.searchSimilar = vi.fn().mockResolvedValueOnce(resultsNoTranscriptions);

    renderWithRouter(<SearchPage />);

    const searchInput = screen.getByPlaceholderText('Enter text to find similar music...');
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.click(screen.getByText('Search'));

    await waitFor(() => {
      expect(screen.queryByText('Transcription:')).not.toBeInTheDocument();
    });
  });

  test('handles results without lyrics', async () => {
    const resultsNoLyrics = [{
      ...mockSearchResults[0],
      lyrics: []
    }];

    mockedApi.searchSimilar = vi.fn().mockResolvedValueOnce(resultsNoLyrics);

    renderWithRouter(<SearchPage />);

    const searchInput = screen.getByPlaceholderText('Enter text to find similar music...');
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.click(screen.getByText('Search'));

    await waitFor(() => {
      expect(screen.queryByText(/Lyrics \(/)).not.toBeInTheDocument();
    });
  });
});