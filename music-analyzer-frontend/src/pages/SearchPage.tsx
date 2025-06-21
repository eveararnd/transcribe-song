import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
import {
  Search as SearchIcon,
  Lyrics as LyricsIcon,
  GraphicEq as SimilarIcon,
  AudioFile as AudioIcon,
} from '@mui/icons-material';
import api from '../services/api';
import { SearchResult } from '../types';

type SearchMode = 'similar' | 'lyrics';

const SearchPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchMode, setSearchMode] = useState<SearchMode>('similar');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    setError(null);
    setResults([]);

    try {
      const searchResults = searchMode === 'similar' 
        ? await api.searchSimilar(query)
        : await api.searchByLyrics(query);
      
      setResults(searchResults);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Search failed');
    } finally {
      setIsSearching(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Search Music
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box mb={2}>
          <ToggleButtonGroup
            value={searchMode}
            exclusive
            onChange={(e, value) => value && setSearchMode(value)}
            aria-label="search mode"
          >
            <ToggleButton value="similar" aria-label="similar search">
              <SimilarIcon sx={{ mr: 1 }} />
              Similar Content
            </ToggleButton>
            <ToggleButton value="lyrics" aria-label="lyrics search">
              <LyricsIcon sx={{ mr: 1 }} />
              Search by Lyrics
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        <Box display="flex" gap={2}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder={
              searchMode === 'similar'
                ? 'Enter text to find similar music...'
                : 'Enter lyrics to search...'
            }
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleSearch();
              }
            }}
          />
          <Button
            variant="contained"
            startIcon={isSearching ? <CircularProgress size={20} /> : <SearchIcon />}
            onClick={handleSearch}
            disabled={isSearching || !query.trim()}
            sx={{ minWidth: 120 }}
          >
            {isSearching ? 'Searching...' : 'Search'}
          </Button>
        </Box>

        {searchMode === 'similar' && (
          <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
            This will search through transcriptions and find music with similar content
          </Typography>
        )}
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {results.length > 0 && (
        <>
          <Typography variant="h6" gutterBottom>
            Found {results.length} results
          </Typography>
          <Grid container spacing={2}>
            {results.map((result) => (
              <Grid item xs={12} md={6} key={result.file.id}>
                <Card>
                  <CardContent>
                    <Box display="flex" alignItems="center" mb={1}>
                      <AudioIcon sx={{ mr: 1 }} />
                      <Typography variant="h6" component="div" sx={{ flex: 1 }}>
                        {result.file.filename}
                      </Typography>
                      {result.similarity_score && (
                        <Chip
                          label={`${(result.similarity_score * 100).toFixed(1)}% match`}
                          color="primary"
                          size="small"
                        />
                      )}
                    </Box>
                    
                    <Box display="flex" gap={1} mb={2}>
                      <Chip label={result.file.filename.split('.').pop()?.toUpperCase() || 'UNKNOWN'} size="small" />
                      <Chip label={formatDuration(result.file.duration)} size="small" />
                      {result.file.genre && <Chip label={result.file.genre} size="small" />}
                    </Box>

                    {result.transcriptions.length > 0 && (
                      <Box mb={2}>
                        <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                          Transcription:
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            display: '-webkit-box',
                            WebkitLineClamp: 3,
                            WebkitBoxOrient: 'vertical',
                          }}
                        >
                          {result.transcriptions[0].text}
                        </Typography>
                      </Box>
                    )}

                    {result.lyrics.length > 0 && (
                      <Box>
                        <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                          Lyrics ({result.lyrics[0].source}):
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            display: '-webkit-box',
                            WebkitLineClamp: 3,
                            WebkitBoxOrient: 'vertical',
                          }}
                        >
                          {result.lyrics[0].lyrics_text}
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                  <CardActions>
                    <Button
                      size="small"
                      onClick={() => navigate(`/file/${result.file.id}`)}
                    >
                      View Details
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </>
      )}

      {!isSearching && query && results.length === 0 && !error && (
        <Box textAlign="center" mt={4}>
          <Typography color="textSecondary">
            No results found. Try a different search query.
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default SearchPage;