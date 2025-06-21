import axios from 'axios';
import { MusicFile, Transcription, Lyrics, SearchResult, UploadResponse, TranscriptionRequest, StorageStats } from '../types';
import { cookieUtils } from '../utils/cookieUtils';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/v2';

class ApiService {
  private getAuthHeader(): string {
    // First try to get auth from cookie
    const cookieHeader = cookieUtils.getAuthHeaderFromCookie();
    if (cookieHeader) {
      return cookieHeader;
    }
    
    // Fall back to sessionStorage for backward compatibility
    const auth = sessionStorage.getItem('auth');
    if (auth) {
      const { username, password } = JSON.parse(auth);
      return 'Basic ' + btoa(`${username}:${password}`);
    }
    return '';
  }

  private get headers() {
    return {
      Authorization: this.getAuthHeader(),
      'Content-Type': 'application/json',
    };
  }

  // File operations
  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
      headers: {
        Authorization: this.getAuthHeader(),
      },
    });
    return response.data;
  }

  async getFiles(limit: number = 100, offset: number = 0): Promise<MusicFile[]> {
    const response = await axios.get(`${API_BASE_URL}/files`, {
      params: { limit, offset },
      headers: this.headers,
    });
    return response.data.files;
  }

  async getFile(fileId: string): Promise<MusicFile> {
    const response = await axios.get(`${API_BASE_URL}/files/${fileId}`, {
      headers: this.headers,
    });
    return response.data;
  }

  async deleteFile(fileId: string): Promise<void> {
    await axios.delete(`${API_BASE_URL}/files/${fileId}`, {
      headers: this.headers,
    });
  }

  async batchDeleteFiles(fileIds: string[]): Promise<any> {
    const response = await axios.post(
      `${API_BASE_URL}/files/batch/delete`,
      { file_ids: fileIds },
      { headers: this.headers }
    );
    return response.data;
  }

  async batchExportFiles(fileIds: string[], format: string = 'tar.gz'): Promise<Blob> {
    const response = await axios.post(
      `${API_BASE_URL}/files/batch/export`,
      { file_ids: fileIds, format },
      { 
        headers: this.headers,
        responseType: 'blob'
      }
    );
    return response.data;
  }

  // Transcription operations
  async transcribeFile(request: TranscriptionRequest): Promise<Transcription> {
    const response = await axios.post(`${API_BASE_URL}/transcribe`, request, {
      headers: this.headers,
    });
    return response.data;
  }

  async getTranscriptions(fileId: string): Promise<Transcription[]> {
    const response = await axios.get(`${API_BASE_URL}/files/${fileId}/transcriptions`, {
      headers: this.headers,
    });
    return response.data;
  }

  // Lyrics operations
  async searchLyrics(fileId: string, useWebSearch: boolean = true): Promise<Lyrics[]> {
    const response = await axios.post(
      `${API_BASE_URL}/search-lyrics`,
      { file_id: fileId, use_web_search: useWebSearch },
      { headers: this.headers }
    );
    return response.data.lyrics;
  }

  async getLyrics(fileId: string): Promise<Lyrics[]> {
    const response = await axios.get(`${API_BASE_URL}/files/${fileId}/lyrics`, {
      headers: this.headers,
    });
    return response.data;
  }

  // Search operations
  async searchSimilar(query: string, limit: number = 10): Promise<SearchResult[]> {
    const response = await axios.post(
      `${API_BASE_URL}/search/similar`,
      { query, limit },
      { headers: this.headers }
    );
    return response.data.results;
  }

  async searchByLyrics(query: string, limit: number = 10): Promise<SearchResult[]> {
    const response = await axios.post(
      `${API_BASE_URL}/search/lyrics`,
      { query, limit },
      { headers: this.headers }
    );
    return response.data.results;
  }

  // Export operations
  async exportFile(fileId: string, format: string): Promise<Blob> {
    const response = await axios.get(`${API_BASE_URL}/export/${fileId}`, {
      params: { format },
      headers: {
        Authorization: this.getAuthHeader(),
      },
      responseType: 'blob',
    });
    return response.data;
  }

  async exportBatch(fileIds: string[], format: string): Promise<Blob> {
    const response = await axios.post(
      `${API_BASE_URL}/export/batch`,
      { file_ids: fileIds, format },
      {
        headers: {
          Authorization: this.getAuthHeader(),
        },
        responseType: 'blob',
      }
    );
    return response.data;
  }

  // Storage operations
  async getStorageStats(): Promise<StorageStats> {
    const response = await axios.get(`${API_BASE_URL}/storage/stats`, {
      headers: this.headers,
    });
    return response.data;
  }

  // Catalog operations
  async getCatalog(): Promise<MusicFile[]> {
    const response = await axios.get(`${API_BASE_URL}/catalog`, {
      headers: this.headers,
    });
    return response.data.files;
  }

  // Health check
  async healthCheck(): Promise<any> {
    const response = await axios.get(`${API_BASE_URL}/health`, {
      headers: this.headers,
    });
    return response.data;
  }

  // Model management
  async getModelsStatus(): Promise<any> {
    const response = await axios.get(`${API_BASE_URL}/models/status`, {
      headers: this.headers,
    });
    return response.data;
  }

  async loadModel(modelType: string): Promise<any> {
    const response = await axios.post(
      `${API_BASE_URL}/models/load`,
      { model_type: modelType },
      { headers: this.headers }
    );
    return response.data;
  }

  async unloadModel(): Promise<any> {
    const response = await axios.post(
      `${API_BASE_URL}/models/unload`,
      {},
      { headers: this.headers }
    );
    return response.data;
  }

  async generateText(prompt: string, maxLength: number = 200): Promise<any> {
    const response = await axios.post(
      `${API_BASE_URL}/models/generate`,
      { prompt, max_length: maxLength },
      { headers: this.headers }
    );
    return response.data;
  }
}

export default new ApiService();
export const api = new ApiService();