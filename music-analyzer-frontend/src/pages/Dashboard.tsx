import React, { useState, useMemo } from 'react';
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
  TableSortLabel,
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
  Checkbox,
  Toolbar,
  alpha,
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
  
  // State for selected files
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  
  // State for sorting
  const [orderBy, setOrderBy] = useState<keyof MusicFile>('created_at');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');
  
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
    async (data: { fileId?: string; fileIds?: string[] }) => {
      if (data.fileIds) {
        return api.batchDeleteFiles(data.fileIds);
      } else if (data.fileId) {
        return api.deleteFile(data.fileId);
      }
      throw new Error('No file ID provided');
    },
    {
      onSuccess: (response, variables) => {
        const isBatch = !!variables.fileIds;
        if (isBatch) {
          setNotification({
            open: true,
            message: `Deleted ${response.total_deleted} files successfully${response.total_failed > 0 ? `, ${response.total_failed} failed` : ''}`,
            severity: response.total_failed > 0 ? 'warning' : 'success',
          });
          setSelectedFiles([]);
        } else {
          setNotification({
            open: true,
            message: 'File deleted successfully',
            severity: 'success',
          });
        }
        // Refresh both files and stats
        refetchFiles();
        queryClient.invalidateQueries('storageStats');
      },
      onError: (error: any) => {
        setNotification({
          open: true,
          message: error.response?.data?.detail || 'Error deleting file(s)',
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
      // Single file delete
      deleteMutation.mutate({ fileId: deleteDialog.file.id });
    } else if (selectedFiles.length > 0) {
      // Batch delete
      deleteMutation.mutate({ fileIds: selectedFiles });
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

  const handleRequestSort = (property: keyof MusicFile) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const sortedFiles = useMemo(() => {
    if (!files) return [];
    
    return [...files].sort((a, b) => {
      let aValue = a[orderBy];
      let bValue = b[orderBy];
      
      // Handle special cases
      if (orderBy === 'created_at') {
        aValue = new Date(aValue as string).getTime();
        bValue = new Date(bValue as string).getTime();
      }
      
      if (aValue === null || aValue === undefined) return 1;
      if (bValue === null || bValue === undefined) return -1;
      
      if (aValue < bValue) {
        return order === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return order === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [files, orderBy, order]);

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
      
      {selectedFiles.length > 0 && (
        <Toolbar
          sx={{
            pl: { sm: 2 },
            pr: { xs: 1, sm: 1 },
            ...(selectedFiles.length > 0 && {
              bgcolor: (theme) =>
                alpha(theme.palette.primary.main, theme.palette.action.activatedOpacity),
            }),
            mb: 2,
          }}
        >
          <Typography
            sx={{ flex: '1 1 100%' }}
            color="inherit"
            variant="subtitle1"
            component="div"
          >
            {selectedFiles.length} selected
          </Typography>
          
          <Tooltip title="Delete selected">
            <IconButton
              onClick={() => {
                setDeleteDialog({
                  open: true,
                  file: null, // Indicates batch delete
                });
              }}
            >
              <DeleteIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Export selected">
            <IconButton
              onClick={async () => {
                try {
                  const blob = await api.batchExportFiles(selectedFiles);
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `music_export_${new Date().toISOString().split('T')[0]}.tar.gz`;
                  a.click();
                  URL.revokeObjectURL(url);
                  setNotification({
                    open: true,
                    message: `Exported ${selectedFiles.length} files successfully`,
                    severity: 'success',
                  });
                } catch (error) {
                  setNotification({
                    open: true,
                    message: 'Failed to export files',
                    severity: 'error',
                  });
                }
              }}
            >
              <DownloadIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      )}
      
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={selectedFiles.length > 0 && selectedFiles.length < (sortedFiles?.length || 0)}
                  checked={sortedFiles?.length > 0 && selectedFiles.length === sortedFiles?.length}
                  onChange={(event) => {
                    if (event.target.checked) {
                      setSelectedFiles(sortedFiles?.map(f => f.id) || []);
                    } else {
                      setSelectedFiles([]);
                    }
                  }}
                />
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'filename'}
                  direction={orderBy === 'filename' ? order : 'asc'}
                  onClick={() => handleRequestSort('filename')}
                >
                  File Name
                </TableSortLabel>
              </TableCell>
              <TableCell>Format</TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'duration'}
                  direction={orderBy === 'duration' ? order : 'asc'}
                  onClick={() => handleRequestSort('duration')}
                >
                  Duration
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'file_size'}
                  direction={orderBy === 'file_size' ? order : 'asc'}
                  onClick={() => handleRequestSort('file_size')}
                >
                  Size
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'genre'}
                  direction={orderBy === 'genre' ? order : 'asc'}
                  onClick={() => handleRequestSort('genre')}
                >
                  Genre
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'created_at'}
                  direction={orderBy === 'created_at' ? order : 'asc'}
                  onClick={() => handleRequestSort('created_at')}
                >
                  Uploaded
                </TableSortLabel>
              </TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedFiles?.map((file: MusicFile) => {
              const isSelected = selectedFiles.includes(file.id);
              return (
              <TableRow 
                key={file.id}
                selected={isSelected}
                hover
              >
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={isSelected}
                    onChange={(event) => {
                      if (event.target.checked) {
                        setSelectedFiles([...selectedFiles, file.id]);
                      } else {
                        setSelectedFiles(selectedFiles.filter(id => id !== file.id));
                      }
                    }}
                  />
                </TableCell>
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
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {(!sortedFiles || sortedFiles.length === 0) && (
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
            {deleteDialog.file 
              ? `Are you sure you want to delete "${deleteDialog.file.filename}"? This action cannot be undone.`
              : `Are you sure you want to delete ${selectedFiles.length} selected files? This action cannot be undone.`
            }
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