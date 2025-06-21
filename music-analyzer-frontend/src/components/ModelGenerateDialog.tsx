/**
 * Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Box,
  Typography,
} from '@mui/material';
import { api } from '../services/api';

interface ModelGenerateDialogProps {
  open: boolean;
  onClose: () => void;
  initialPrompt?: string;
  onGenerated?: (response: string) => void;
}

export const ModelGenerateDialog: React.FC<ModelGenerateDialogProps> = ({
  open,
  onClose,
  initialPrompt = '',
  onGenerated,
}) => {
  const [prompt, setPrompt] = useState(initialPrompt);
  const [maxLength, setMaxLength] = useState(200);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentModel, setCurrentModel] = useState<string | null>(null);
  const [response, setResponse] = useState<string>('');

  useEffect(() => {
    if (open) {
      fetchCurrentModel();
      setPrompt(initialPrompt);
      setResponse('');
      setError(null);
    }
  }, [open, initialPrompt]);

  const fetchCurrentModel = async () => {
    try {
      const status = await api.getModelsStatus();
      setCurrentModel(status.current_model);
      if (!status.current_model) {
        setError('No model is currently loaded. Please load a model first.');
      }
    } catch (err) {
      setError('Failed to check model status');
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim() || !currentModel) return;

    setLoading(true);
    setError(null);
    setResponse('');

    try {
      const result = await api.generateText(prompt, maxLength);
      setResponse(result.response || result.text || result);
      if (onGenerated) {
        onGenerated(result.response || result.text || result);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate text');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Generate Text with AI Model
        {currentModel && (
          <Typography variant="body2" color="text.secondary">
            Using: {currentModel}
          </Typography>
        )}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <TextField
            fullWidth
            multiline
            rows={4}
            label="Prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter your prompt here..."
            disabled={loading || !currentModel}
            sx={{ mb: 2 }}
          />

          <FormControl sx={{ minWidth: 120, mr: 2 }}>
            <InputLabel>Max Length</InputLabel>
            <Select
              value={maxLength}
              onChange={(e) => setMaxLength(Number(e.target.value))}
              disabled={loading}
            >
              <MenuItem value={50}>50 tokens</MenuItem>
              <MenuItem value={100}>100 tokens</MenuItem>
              <MenuItem value={200}>200 tokens</MenuItem>
              <MenuItem value={500}>500 tokens</MenuItem>
              <MenuItem value={1000}>1000 tokens</MenuItem>
            </Select>
          </FormControl>

          {response && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                Generated Response:
              </Typography>
              <Box
                sx={{
                  p: 2,
                  bgcolor: 'background.default',
                  borderRadius: 1,
                  border: '1px solid',
                  borderColor: 'divider',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {response}
              </Box>
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        <Button
          onClick={handleGenerate}
          variant="contained"
          disabled={!prompt.trim() || loading || !currentModel}
        >
          {loading ? (
            <>
              <CircularProgress size={20} sx={{ mr: 1 }} />
              Generating...
            </>
          ) : (
            'Generate'
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
};