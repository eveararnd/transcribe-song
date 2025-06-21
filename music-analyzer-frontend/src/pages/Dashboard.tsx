import React from 'react';
import { useQuery } from 'react-query';
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
} from '@mui/material';
import { 
  Visibility as ViewIcon,
  GetApp as DownloadIcon,
  AudioFile as AudioIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import api from '../services/api';
import { MusicFile, StorageStats } from '../types';
import { ModelSelector } from '../components/ModelSelector';
import { parseDate } from '../utils/dateUtils';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  
  const { data: files, isLoading: filesLoading, error: filesError } = useQuery(
    'files',
    () => api.getFiles(50)
  );

  const { data: stats, isLoading: statsLoading } = useQuery(
    'storageStats',
    () => api.getStorageStats()
  );

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
                    {file.original_filename}
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip label={file.file_format?.toUpperCase()} size="small" />
                </TableCell>
                <TableCell>{formatDuration(file.duration)}</TableCell>
                <TableCell>{formatBytes(file.file_size)}</TableCell>
                <TableCell>{file.genre || '-'}</TableCell>
                <TableCell>
                  {format(parseDate(file.uploaded_at), 'MMM dd, yyyy')}
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => navigate(`/file/${file.id}`)}
                    title="View Details"
                  >
                    <ViewIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={async () => {
                      const blob = await api.exportFile(file.id, 'json');
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `${file.original_filename}.json`;
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                    title="Download"
                  >
                    <DownloadIcon />
                  </IconButton>
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
    </Box>
  );
};

export default Dashboard;