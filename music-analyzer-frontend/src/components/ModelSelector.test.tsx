/**
 * Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ModelSelector } from './ModelSelector';
import { api } from '../services/api';

// Mock the API
vi.mock('../services/api');

const mockApi = api as any;

describe('ModelSelector', () => {
  const mockModelsStatus = {
    current_model: 'phi-4-reasoning',
    device: 'cuda',
    models: {
      'gemma-3-12b': {
        model_id: 'google/gemma-3-12b-it',
        type: 'causal-lm',
        loaded: false,
        downloaded: true,
        local_path: '/path/to/gemma',
        inference_available: true,
      },
      'phi-4-multimodal': {
        model_id: 'microsoft/phi-4-multimodal',
        type: 'multimodal',
        loaded: false,
        downloaded: true,
        local_path: '/path/to/phi4-multi',
        inference_available: true,
      },
      'phi-4-reasoning': {
        model_id: 'microsoft/phi-4-reasoning',
        type: 'causal-lm',
        loaded: true,
        downloaded: true,
        local_path: '/path/to/phi4-reasoning',
        inference_available: true,
        gpu_memory_mb: 8192,
      },
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.getModelsStatus = vi.fn().mockResolvedValue(mockModelsStatus);
    mockApi.loadModel = vi.fn();
    mockApi.unloadModel = vi.fn();
  });

  it('renders model selector with current status', async () => {
    render(<ModelSelector />);

    await waitFor(() => {
      expect(screen.getByText('Model Selection')).toBeInTheDocument();
    });

    // Check device display
    expect(screen.getByText('Device: CUDA')).toBeInTheDocument();

    // Check current model display
    expect(screen.getByText('phi-4-reasoning')).toBeInTheDocument();
    expect(screen.getByText('GPU Memory: 8192 MB')).toBeInTheDocument();
  });

  it('displays available models in dropdown', async () => {
    render(<ModelSelector />);

    await waitFor(() => {
      expect(screen.getByText('Select Model')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');
    fireEvent.mouseDown(select);

    await waitFor(() => {
      expect(screen.getByText('Gemma 3 12B-IT')).toBeInTheDocument();
      expect(screen.getByText('Phi-4 Multimodal')).toBeInTheDocument();
      expect(screen.getAllByText('Phi-4 Reasoning')[0]).toBeInTheDocument();
    });
  });

  it('loads a model when Load Model button is clicked', async () => {
    mockApi.loadModel.mockResolvedValue({
      status: 'success',
      message: 'gemma-3-12b loaded successfully',
    });

    render(<ModelSelector />);

    await waitFor(() => {
      expect(screen.getByText('Select Model')).toBeInTheDocument();
    });

    // Select Gemma model
    const select = screen.getByRole('combobox');
    fireEvent.mouseDown(select);
    fireEvent.click(screen.getByText('Gemma 3 12B-IT'));

    // Click Load Model
    const loadButton = screen.getByText('Load Model');
    fireEvent.click(loadButton);

    await waitFor(() => {
      expect(mockApi.loadModel).toHaveBeenCalledWith('gemma-3-12b');
    });

    // Check success message
    await waitFor(() => {
      expect(screen.getByText('Successfully loaded gemma-3-12b')).toBeInTheDocument();
    });
  });

  it('unloads current model when Unload Current button is clicked', async () => {
    mockApi.unloadModel.mockResolvedValue({
      status: 'success',
      message: 'Model unloaded successfully',
    });

    render(<ModelSelector />);

    await waitFor(() => {
      expect(screen.getByText('Unload Current')).toBeInTheDocument();
    });

    const unloadButton = screen.getByText('Unload Current');
    fireEvent.click(unloadButton);

    await waitFor(() => {
      expect(mockApi.unloadModel).toHaveBeenCalled();
    });

    // Check success message
    await waitFor(() => {
      expect(screen.getByText('Model unloaded successfully')).toBeInTheDocument();
    });
  });

  it('shows error when model loading fails', async () => {
    mockApi.loadModel.mockRejectedValue({
      response: {
        data: {
          detail: 'Failed to load model: Out of memory',
        },
      },
    });

    render(<ModelSelector />);

    await waitFor(() => {
      expect(screen.getByText('Select Model')).toBeInTheDocument();
    });

    // Select and try to load
    const select = screen.getByRole('combobox');
    fireEvent.mouseDown(select);
    fireEvent.click(screen.getByText('Gemma 3 12B-IT'));
    fireEvent.click(screen.getByText('Load Model'));

    await waitFor(() => {
      expect(screen.getByText('Failed to load model: Out of memory')).toBeInTheDocument();
    });
  });

  it('disables Load Model button when current model is selected', async () => {
    render(<ModelSelector />);

    await waitFor(() => {
      expect(screen.getByText('Select Model')).toBeInTheDocument();
    });

    // Select current model (phi-4-reasoning)
    const select = screen.getByRole('combobox');
    fireEvent.mouseDown(select);
    fireEvent.click(screen.getAllByText('Phi-4 Reasoning')[1]);

    const loadButton = screen.getByText('Load Model');
    expect(loadButton).toBeDisabled();
  });

  it('shows loading state during model operations', async () => {
    let resolveLoad: any;
    mockApi.loadModel.mockImplementation(
      () => new Promise((resolve) => {
        resolveLoad = resolve;
      })
    );

    render(<ModelSelector />);

    await waitFor(() => {
      expect(screen.getByText('Select Model')).toBeInTheDocument();
    });

    // Select and load
    const select = screen.getByRole('combobox');
    fireEvent.mouseDown(select);
    fireEvent.click(screen.getByText('Gemma 3 12B-IT'));
    fireEvent.click(screen.getByText('Load Model'));

    // Check loading state
    await waitFor(() => {
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    // Resolve the promise
    resolveLoad({ status: 'success' });

    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });
  });
});