/**
 * Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import axios from 'axios';
import api from './api';

// Mock axios
vi.mock('axios');
const mockedAxios = axios as any;

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    // Set up auth for tests
    sessionStorage.setItem('auth', JSON.stringify({ username: 'testuser', password: 'testpass' }));
  });

  describe('uploadFile', () => {
    test('uploads file successfully', async () => {
      const mockResponse = {
        data: {
          file_id: 'test-id',
          filename: 'test.mp3',
          genre: 'rock',
          size: 1024,
          duration: 180,
          hash: 'testhash'
        }
      };
      mockedAxios.post = vi.fn().mockResolvedValueOnce(mockResponse);

      const file = new File(['test'], 'test.mp3', { type: 'audio/mp3' });
      const result = await api.uploadFile(file);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v2/upload',
        expect.any(FormData),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Basic ' + btoa('testuser:testpass')
          })
        })
      );
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getFiles', () => {
    test('fetches files with default parameters', async () => {
      const mockFiles = [
        { id: '1', original_filename: 'file1.mp3' },
        { id: '2', original_filename: 'file2.mp3' }
      ];
      mockedAxios.get = vi.fn().mockResolvedValueOnce({ 
        data: { 
          files: mockFiles,
          total: 2,
          limit: 100,
          offset: 0
        } 
      });

      const result = await api.getFiles();

      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/api/v2/files',
        expect.objectContaining({
          params: { limit: 100, offset: 0 }
        })
      );
      expect(result).toEqual(mockFiles);
    });

    test('fetches files with custom parameters', async () => {
      mockedAxios.get = vi.fn().mockResolvedValueOnce({ 
        data: { 
          files: [],
          total: 0,
          limit: 50,
          offset: 10
        } 
      });

      await api.getFiles(50, 10);

      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/api/v2/files',
        expect.objectContaining({
          params: { limit: 50, offset: 10 }
        })
      );
    });
  });

  describe('transcribeFile', () => {
    test('sends transcription request', async () => {
      const mockTranscription = {
        id: 'trans-1',
        text: 'Transcribed text',
        language: 'en',
        confidence: 0.95
      };
      mockedAxios.post = vi.fn().mockResolvedValueOnce({ data: mockTranscription });

      const request = { file_id: 'test-id' };
      const result = await api.transcribeFile(request);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v2/transcribe',
        request,
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      );
      expect(result).toEqual(mockTranscription);
    });
  });

  describe('searchLyrics', () => {
    test('searches lyrics with web search enabled', async () => {
      const mockLyrics = [
        { id: 'lyrics-1', source: 'genius', lyrics_text: 'Test lyrics' }
      ];
      mockedAxios.post = vi.fn().mockResolvedValueOnce({ data: { lyrics: mockLyrics } });

      const result = await api.searchLyrics('file-id');

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v2/search-lyrics',
        { file_id: 'file-id', use_web_search: true },
        expect.any(Object)
      );
      expect(result).toEqual(mockLyrics);
    });
  });

  describe('exportFile', () => {
    test('exports file in specified format', async () => {
      const mockBlob = new Blob(['export data']);
      mockedAxios.get = vi.fn().mockResolvedValueOnce({ data: mockBlob });

      const result = await api.exportFile('file-id', 'json');

      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/api/v2/export/file-id',
        expect.objectContaining({
          params: { format: 'json' },
          responseType: 'blob'
        })
      );
      expect(result).toEqual(mockBlob);
    });
  });

  describe('searchSimilar', () => {
    test('searches for similar content', async () => {
      const mockResults = {
        results: [
          { file: { id: '1', original_filename: 'similar.mp3' }, transcriptions: [], lyrics: [] }
        ]
      };
      mockedAxios.post = vi.fn().mockResolvedValueOnce({ data: mockResults });

      const result = await api.searchSimilar('test query');

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v2/search/similar',
        { query: 'test query', limit: 10 },
        expect.any(Object)
      );
      expect(result).toEqual(mockResults.results);
    });
  });

  describe('getStorageStats', () => {
    test('fetches storage statistics', async () => {
      const mockStats = {
        total_files: 100,
        total_size: 1024000,
        by_format: { mp3: { count: 50, size: 512000 } },
        by_genre: { rock: { count: 30, size: 307200 } }
      };
      mockedAxios.get = vi.fn().mockResolvedValueOnce({ data: mockStats });

      const result = await api.getStorageStats();

      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/api/v2/storage/stats',
        expect.any(Object)
      );
      expect(result).toEqual(mockStats);
    });
  });

  describe('deleteFile', () => {
    test('deletes file by id', async () => {
      mockedAxios.delete = vi.fn().mockResolvedValueOnce({ data: {} });

      await api.deleteFile('file-id');

      expect(mockedAxios.delete).toHaveBeenCalledWith(
        '/api/v2/files/file-id',
        expect.any(Object)
      );
    });
  });

  describe('exportBatch', () => {
    test('exports multiple files', async () => {
      const mockBlob = new Blob(['batch export']);
      mockedAxios.post = vi.fn().mockResolvedValueOnce({ data: mockBlob });

      const fileIds = ['id1', 'id2', 'id3'];
      const result = await api.exportBatch(fileIds, 'tar.gz');

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v2/export/batch',
        { file_ids: fileIds, format: 'tar.gz' },
        expect.objectContaining({
          responseType: 'blob'
        })
      );
      expect(result).toEqual(mockBlob);
    });
  });

  describe('authentication', () => {
    test('includes auth header when credentials are present', async () => {
      mockedAxios.get = vi.fn().mockResolvedValueOnce({ 
        data: { files: [], total: 0, limit: 100, offset: 0 } 
      });

      await api.getFiles();

      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Basic ' + btoa('testuser:testpass')
          })
        })
      );
    });

    test('sends empty auth header when no credentials', async () => {
      sessionStorage.clear();
      mockedAxios.get = vi.fn().mockResolvedValueOnce({ 
        data: { files: [], total: 0, limit: 100, offset: 0 } 
      });

      await api.getFiles();

      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: ''
          })
        })
      );
    });
  });
});