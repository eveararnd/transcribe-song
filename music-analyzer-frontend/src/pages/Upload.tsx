import React, { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  AudioFile as AudioIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import api from '../services/api';

interface FileUpload {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  fileId?: string;
  error?: string;
}

const Upload: React.FC = () => {
  const navigate = useNavigate();
  const [uploads, setUploads] = useState<FileUpload[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newUploads = acceptedFiles.map((file) => ({
      file,
      status: 'pending' as const,
      progress: 0,
    }));
    setUploads((prev) => [...prev, ...newUploads]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.flac', '.wav', '.m4a', '.ogg', '.opus', '.wma'],
    },
    multiple: true,
  });

  const uploadFiles = async () => {
    setIsUploading(true);
    const pendingUploads = uploads.filter((u) => u.status === 'pending');

    for (let i = 0; i < pendingUploads.length; i++) {
      const upload = pendingUploads[i];
      const index = uploads.indexOf(upload);

      try {
        setUploads((prev) => {
          const updated = [...prev];
          updated[index] = { ...upload, status: 'uploading', progress: 50 };
          return updated;
        });

        const response = await api.uploadFile(upload.file);

        setUploads((prev) => {
          const updated = [...prev];
          updated[index] = {
            ...upload,
            status: 'success',
            progress: 100,
            fileId: response.file_id,
          };
          return updated;
        });
      } catch (error: any) {
        setUploads((prev) => {
          const updated = [...prev];
          updated[index] = {
            ...upload,
            status: 'error',
            progress: 0,
            error: error.response?.data?.detail || 'Upload failed',
          };
          return updated;
        });
      }
    }

    setIsUploading(false);
  };

  const successfulUploads = uploads.filter((u) => u.status === 'success');
  const pendingUploads = uploads.filter((u) => u.status === 'pending');

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Upload Music Files
      </Typography>

      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          mb: 3,
          textAlign: 'center',
          cursor: 'pointer',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'divider',
        }}
      >
        <input {...getInputProps()} />
        <UploadIcon sx={{ fontSize: 48, color: 'action.active', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive
            ? 'Drop the files here...'
            : 'Drag & drop music files here, or click to select'}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          Supported formats: MP3, FLAC, WAV, M4A, OGG, OPUS, WMA
        </Typography>
      </Paper>

      {uploads.length > 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Upload Queue
          </Typography>
          <List>
            {uploads.map((upload, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  {upload.status === 'success' ? (
                    <SuccessIcon color="success" />
                  ) : upload.status === 'error' ? (
                    <ErrorIcon color="error" />
                  ) : (
                    <AudioIcon />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={upload.file.name}
                  secondary={
                    upload.error || 
                    (upload.fileId && `File ID: ${upload.fileId}`) ||
                    `${(upload.file.size / 1024 / 1024).toFixed(2)} MB`
                  }
                />
                <Chip
                  label={upload.status}
                  size="small"
                  color={
                    upload.status === 'success'
                      ? 'success'
                      : upload.status === 'error'
                      ? 'error'
                      : 'default'
                  }
                />
              </ListItem>
            ))}
          </List>

          {pendingUploads.length > 0 && (
            <Box mt={2}>
              <Button
                variant="contained"
                fullWidth
                onClick={uploadFiles}
                disabled={isUploading}
                startIcon={isUploading ? <CircularProgress size={20} /> : <UploadIcon />}
              >
                {isUploading ? 'Uploading...' : `Upload ${pendingUploads.length} Files`}
              </Button>
            </Box>
          )}

          {successfulUploads.length > 0 && (
            <Box mt={2}>
              <Alert severity="success">
                {successfulUploads.length} files uploaded successfully!
              </Alert>
              {successfulUploads.length === 1 && (
                <Button
                  variant="outlined"
                  fullWidth
                  sx={{ mt: 1 }}
                  onClick={() => navigate(`/file/${successfulUploads[0].fileId}`)}
                >
                  View File Details
                </Button>
              )}
            </Box>
          )}
        </Paper>
      )}
    </Box>
  );
};

export default Upload;