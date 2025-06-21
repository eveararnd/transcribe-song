import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Button,
  Tooltip,
  Snackbar,
} from '@mui/material';
import { 
  Visibility as ViewIcon,
  GetApp as DownloadIcon,
  AudioFile as AudioIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import api from '../services/api';
import { MusicFile, StorageStats } from '../types';
import { ModelSelector } from '../components/ModelSelector';
import { parseDate } from '../utils/dateUtils';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  // State for delete confirmation dialog
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; file: MusicFile | null }>({
    open: false,
    file: null,
  });
  
  // State for notifications
  const [notification, setNotification] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });
  
  const { data: files, isLoading: filesLoading, error: filesError, refetch: refetchFiles } = useQuery(
    'files',
    () => api.getFiles(50)
  );

  const { data: stats, isLoading: statsLoading } = useQuery(
    'storageStats',
    () => api.getStorageStats()
  );

  // Delete mutation
  const deleteMutation = useMutation(
    (fileId: string) => api.deleteFile(fileId),
    {
      onSuccess: () => {
        setNotification({
          open: true,
          message: 'File deleted successfully',
          severity: 'success',
        });
        // Refresh both files and stats
        refetchFiles();
        queryClient.invalidateQueries('storageStats');
      },
      onError: (error: any) => {
        setNotification({
          open: true,
          message: error.response?.data?.detail || 'Error deleting file',
          severity: 'error',
        });
      },
    }
  );

  const handleDeleteClick = (file: MusicFile) => {
    setDeleteDialog({ open: true, file });
  };

  const handleDeleteConfirm = () => {
    if (deleteDialog.file) {
      deleteMutation.mutate(deleteDialog.file.id);
    }
    setDeleteDialog({ open: false, file: null });
  };

  const handleDeleteCancel = () => {
    setDeleteDialog({ open: false, file: null });
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (filesLoading || statsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (filesError) {
    return (
      <Alert severity="error">
        Error loading files. Please check your authentication and try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {/* Model Selector */}
      <ModelSelector />

      {/* Stats Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Files
              </Typography>
              <Typography variant="h4">
                {stats?.total_files || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Size
              </Typography>
              <Typography variant="h4">
                {formatBytes(stats?.total_size || 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                File Formats
              </Typography>
              <Typography variant="h4">
                {Object.keys(stats?.by_format || {}).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Genres
              </Typography>
              <Typography variant="h4">
                {Object.keys(stats?.by_genre || {}).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Files Table */}
      <Typography variant="h5" gutterBottom>
        Recent Files
      </Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>File Name</TableCell>
              <TableCell>Format</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Genre</TableCell>
              <TableCell>Uploaded</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {files?.map((file: MusicFile) => (
              <TableRow key={file.id}>
                <TableCell>
                  <Box display="flex" alignItems="center">
                    <AudioIcon sx={{ mr: 1 }} />
                    {file.filename}
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip label={file.filename.split('.').pop()?.toUpperCase() || 'UNKNOWN'} size="small" />
                </TableCell>
                <TableCell>{formatDuration(file.duration)}</TableCell>
                <TableCell>{formatBytes(file.file_size)}</TableCell>
                <TableCell>{file.genre || '-'}</TableCell>
                <TableCell>
                  {format(parseDate(file.created_at), 'MMM dd, yyyy')}
                </TableCell>
                <TableCell>
                  <Tooltip title="View Details">
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/file/${file.id}`)}
                    >
                      <ViewIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Download">
                    <IconButton
                      size="small"
                      onClick={async () => {
                        const blob = await api.exportFile(file.id, 'json');
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `${file.filename}.json`;
                        a.click();
                        URL.revokeObjectURL(url);
                      }}
                    >
                      <DownloadIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete file">
                    <IconButton
                      size="small"
                      onClick={() => handleDeleteClick(file)}
                      sx={{
                        '&:hover': {
                          color: 'error.main',
                        },
                      }}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {(!files || files.length === 0) && (
        <Box mt={4} textAlign="center">
          <Typography color="textSecondary">
            No files uploaded yet. Start by uploading a music file.
          </Typography>
        </Box>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialog.open}
        onClose={handleDeleteCancel}
        aria-labelledby="delete-dialog-title"
        aria-describedby="delete-dialog-description"
      >
        <DialogTitle id="delete-dialog-title">
          Confirm Delete
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="delete-dialog-description">
            Are you sure you want to delete "{deleteDialog.file?.filename}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} color="primary">
            Cancel
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" autoFocus>
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={() => setNotification({ ...notification, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setNotification({ ...notification, open: false })}
          severity={notification.severity}
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Dashboard;