/**
 * Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Typography,
  Stack,
  Paper,
  Grid
} from '@mui/material';
import { api } from '../services/api';

interface ModelInfo {
  model_id: string;
  type: string;
  loaded: boolean;
  downloaded: boolean;
  local_path: string;
  inference_available: boolean;
  gpu_memory_mb?: number;
}

interface ModelsStatus {
  current_model: string | null;
  device: string;
  models: Record<string, ModelInfo>;
}

export const ModelSelector: React.FC = () => {
  const [modelsStatus, setModelsStatus] = useState<ModelsStatus | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>('phi-4-reasoning');
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingModel, setLoadingModel] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Available models
  const availableModels = [
    { id: 'gemma-3-12b', name: 'Gemma 3 12B-IT', description: 'General purpose, instruction following' },
    { id: 'phi-4-multimodal', name: 'Phi-4 Multimodal', description: 'Text, vision, and audio processing' },
    { id: 'phi-4-reasoning', name: 'Phi-4 Reasoning', description: 'Advanced reasoning and problem solving' }
  ];

  // Fetch models status
  const fetchModelsStatus = async () => {
    try {
      const status = await api.getModelsStatus();
      setModelsStatus(status);
      if (status.current_model) {
        setSelectedModel(status.current_model);
      }
    } catch (err) {
      setError('Failed to fetch models status');
    }
  };

  useEffect(() => {
    fetchModelsStatus();
    // Poll for status updates every 5 seconds
    const interval = setInterval(fetchModelsStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // Auto-load phi-4-reasoning if not loaded
  useEffect(() => {
    if (modelsStatus && !modelsStatus.current_model && selectedModel === 'phi-4-reasoning') {
      const phi4Status = modelsStatus.models['phi-4-reasoning'];
      if (phi4Status && phi4Status.downloaded && !phi4Status.loaded && !loading) {
        // Auto-load phi-4-reasoning
        handleLoadModel();
      }
    }
  }, [modelsStatus, selectedModel, loading]);

  const handleLoadModel = async () => {
    if (!selectedModel || loadingModel) return;
    
    setLoading(true);
    setLoadingModel(selectedModel);
    setError(null);
    setSuccess(null);

    try {
      await api.loadModel(selectedModel);
      setSuccess(`Successfully loaded ${selectedModel}`);
      await fetchModelsStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to load ${selectedModel}`);
    } finally {
      setLoading(false);
      setLoadingModel(null);
    }
  };

  const handleUnloadModel = async () => {
    if (!modelsStatus?.current_model || loadingModel) return;
    
    setLoading(true);
    setLoadingModel('unloading');
    setError(null);
    setSuccess(null);

    try {
      await api.unloadModel();
      setSuccess('Model unloaded successfully');
      setSelectedModel('');
      await fetchModelsStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to unload model');
    } finally {
      setLoading(false);
      setLoadingModel(null);
    }
  };

  const getModelStatus = (modelId: string) => {
    if (!modelsStatus) return null;
    return modelsStatus.models[modelId];
  };

  const renderModelChip = (modelId: string) => {
    const status = getModelStatus(modelId);
    if (!status) return null;

    if (status.loaded) {
      return (
        <Chip
          label="Loaded"
          color="success"
          size="small"
          sx={{ ml: 1 }}
        />
      );
    } else if (status.downloaded) {
      return (
        <Chip
          label="Available"
          color="info"
          size="small"
          sx={{ ml: 1 }}
        />
      );
    } else {
      return (
        <Chip
          label="Not Downloaded"
          color="default"
          size="small"
          sx={{ ml: 1 }}
        />
      );
    }
  };

  if (!modelsStatus) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Model Selection
      </Typography>
      
      {/* Current Status */}
      <Box mb={3}>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Device: {modelsStatus.device.toUpperCase()}
        </Typography>
        {modelsStatus.current_model && (
          <Box display="flex" alignItems="center" mb={2}>
            <Typography variant="body2" color="text.secondary">
              Current Model:
            </Typography>
            <Chip
              label={modelsStatus.current_model}
              color="primary"
              size="small"
              sx={{ ml: 1 }}
            />
            {modelsStatus.models[modelsStatus.current_model]?.gpu_memory_mb && (
              <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
                GPU Memory: {Math.round(modelsStatus.models[modelsStatus.current_model].gpu_memory_mb || 0)} MB
              </Typography>
            )}
          </Box>
        )}
      </Box>

      <Grid container spacing={2} alignItems="center">
        <Grid item xs={12} md={6}>
          <FormControl fullWidth variant="outlined">
            <InputLabel id="model-select-label">Select Model</InputLabel>
            <Select
              labelId="model-select-label"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              label="Select Model"
              disabled={loading}
            >
              {availableModels.map((model) => (
                <MenuItem key={model.id} value={model.id}>
                  <Box display="flex" alignItems="center" width="100%">
                    <Box flex={1}>
                      <Typography variant="body1">{model.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {model.description}
                      </Typography>
                    </Box>
                    {renderModelChip(model.id)}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Stack direction="row" spacing={2}>
            <Button
              variant="contained"
              onClick={handleLoadModel}
              disabled={!selectedModel || loading || selectedModel === modelsStatus.current_model}
              fullWidth
            >
              {loadingModel && loadingModel !== 'unloading' ? (
                <>
                  <CircularProgress size={20} sx={{ mr: 1 }} />
                  Loading...
                </>
              ) : (
                'Load Model'
              )}
            </Button>
            
            <Button
              variant="outlined"
              color="secondary"
              onClick={handleUnloadModel}
              disabled={!modelsStatus.current_model || loading}
              fullWidth
            >
              {loadingModel === 'unloading' ? (
                <>
                  <CircularProgress size={20} sx={{ mr: 1 }} />
                  Unloading...
                </>
              ) : (
                'Unload Current'
              )}
            </Button>
          </Stack>
        </Grid>
      </Grid>

      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mt: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}
    </Paper>
  );
};