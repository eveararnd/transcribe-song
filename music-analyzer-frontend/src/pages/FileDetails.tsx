import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation } from 'react-query';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Chip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Transcribe as TranscribeIcon,
  Lyrics as LyricsIcon,
  GetApp as DownloadIcon,
  Delete as DeleteIcon,
  AudioFile as AudioIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import api from '../services/api';
import { MusicFile, Transcription, Lyrics, ExportFormat } from '../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const exportFormats: ExportFormat[] = [
  { format: 'json', label: 'JSON', description: 'Complete data in JSON format' },
  { format: 'csv', label: 'CSV', description: 'Spreadsheet format' },
  { format: 'xlsx', label: 'Excel', description: 'Excel workbook' },
  { format: 'zip', label: 'ZIP', description: 'Complete export with audio' },
  { format: 'tar.gz', label: 'TAR.GZ (Original)', description: 'Original audio files' },
  { format: 'mono_tar.gz', label: 'TAR.GZ (Mono)', description: 'Mono files with metadata' },
];

const FileDetails: React.FC = () => {
  const { fileId } = useParams<{ fileId: string }>();
  const [tabValue, setTabValue] = useState(0);
  const [exportAnchorEl, setExportAnchorEl] = useState<null | HTMLElement>(null);

  const { data: file, isLoading, error } = useQuery(
    ['file', fileId],
    () => api.getFile(fileId!),
    { enabled: !!fileId }
  );

  const { data: transcriptions } = useQuery(
    ['transcriptions', fileId],
    () => api.getTranscriptions(fileId!),
    { enabled: !!fileId }
  );

  const { data: lyrics } = useQuery(
    ['lyrics', fileId],
    () => api.getLyrics(fileId!),
    { enabled: !!fileId }
  );

  const transcribeMutation = useMutation(
    () => api.transcribeFile({ file_id: fileId! }),
    {
      onSuccess: () => {
        // Refetch transcriptions
        window.location.reload();
      },
    }
  );

  const searchLyricsMutation = useMutation(
    () => api.searchLyrics(fileId!),
    {
      onSuccess: () => {
        // Refetch lyrics
        window.location.reload();
      },
    }
  );

  const handleExport = async (format: string) => {
    try {
      const blob = await api.exportFile(fileId!, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${file?.original_filename || 'export'}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
    setExportAnchorEl(null);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !file) {
    return <Alert severity="error">Failed to load file details</Alert>;
  }

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

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <AudioIcon sx={{ fontSize: 40, mr: 2 }} />
        <Box flex={1}>
          <Typography variant="h4">{file.original_filename}</Typography>
          <Typography variant="body2" color="textSecondary">
            Uploaded {format(new Date(file.uploaded_at), 'PPpp')}
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={(e) => setExportAnchorEl(e.currentTarget)}
          sx={{ mr: 1 }}
        >
          Export
        </Button>
      </Box>

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                File Information
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Format
                  </Typography>
                  <Box>
                    <Chip label={file.file_format?.toUpperCase()} size="small" />
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Duration
                  </Typography>
                  <Typography variant="body1">{formatDuration(file.duration)}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Size
                  </Typography>
                  <Typography variant="body1">{formatBytes(file.file_size)}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Sample Rate
                  </Typography>
                  <Typography variant="body1">{file.sample_rate} Hz</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Channels
                  </Typography>
                  <Typography variant="body1">
                    {file.channels === 1 ? 'Mono' : file.channels === 2 ? 'Stereo' : `${file.channels} channels`}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Genre
                  </Typography>
                  <Typography variant="body1">{file.genre || 'Unknown'}</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Actions
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Button
                  variant="contained"
                  startIcon={<TranscribeIcon />}
                  onClick={() => transcribeMutation.mutate()}
                  disabled={transcribeMutation.isLoading}
                >
                  {transcribeMutation.isLoading ? 'Transcribing...' : 'Transcribe Audio'}
                </Button>
                <Button
                  variant="contained"
                  color="secondary"
                  startIcon={<LyricsIcon />}
                  onClick={() => searchLyricsMutation.mutate()}
                  disabled={searchLyricsMutation.isLoading}
                >
                  {searchLyricsMutation.isLoading ? 'Searching...' : 'Search for Lyrics'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ width: '100%' }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label={`Transcriptions (${transcriptions?.length || 0})`} />
          <Tab label={`Lyrics (${lyrics?.length || 0})`} />
          <Tab label="Metadata" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          {transcriptions && transcriptions.length > 0 ? (
            transcriptions.map((transcription: Transcription) => (
              <Paper key={transcription.id} sx={{ p: 2, mb: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Box>
                    <Chip
                      label={`${transcription.language?.toUpperCase() || 'EN'}`}
                      size="small"
                      sx={{ mr: 1 }}
                    />
                    <Chip
                      label={`Confidence: ${(transcription.confidence * 100).toFixed(1)}%`}
                      size="small"
                      color={transcription.confidence > 0.8 ? 'success' : 'warning'}
                    />
                  </Box>
                  <Typography variant="caption" color="textSecondary">
                    {format(new Date(transcription.created_at), 'PPp')}
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {transcription.text}
                </Typography>
              </Paper>
            ))
          ) : (
            <Alert severity="info">
              No transcriptions yet. Click "Transcribe Audio" to generate a transcription.
            </Alert>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {lyrics && lyrics.length > 0 ? (
            lyrics.map((lyric: Lyrics) => (
              <Paper key={lyric.id} sx={{ p: 2, mb: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Box>
                    <Chip label={lyric.source} size="small" sx={{ mr: 1 }} />
                    <Chip
                      label={`Confidence: ${(lyric.confidence * 100).toFixed(1)}%`}
                      size="small"
                      color={lyric.confidence > 0.8 ? 'success' : 'warning'}
                    />
                  </Box>
                  <Typography variant="caption" color="textSecondary">
                    {format(new Date(lyric.created_at), 'PPp')}
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {lyric.lyrics_text}
                </Typography>
              </Paper>
            ))
          ) : (
            <Alert severity="info">
              No lyrics found yet. Click "Search for Lyrics" to find lyrics online.
            </Alert>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <pre style={{ overflow: 'auto' }}>
            {JSON.stringify(file.metadata || {}, null, 2)}
          </pre>
        </TabPanel>
      </Paper>

      <Menu
        anchorEl={exportAnchorEl}
        open={Boolean(exportAnchorEl)}
        onClose={() => setExportAnchorEl(null)}
      >
        {exportFormats.map((format) => (
          <MenuItem key={format.format} onClick={() => handleExport(format.format)}>
            <ListItemText primary={format.label} secondary={format.description} />
          </MenuItem>
        ))}
      </Menu>
    </Box>
  );
};

export default FileDetails;