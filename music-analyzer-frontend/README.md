# Music Analyzer Frontend

A React/TypeScript frontend for the Music Analyzer V2 API.

## Features

- **Dashboard**: Overview of uploaded files and storage statistics
- **Upload**: Drag-and-drop interface for uploading music files
- **File Details**: View file information, transcriptions, and lyrics
- **Search**: Search for similar music by content or lyrics
- **Export**: Download files in various formats (JSON, CSV, Excel, ZIP, TAR.GZ)

## Tech Stack

- React 18
- TypeScript
- Material-UI (MUI)
- React Router
- React Query
- Axios
- react-dropzone
- date-fns

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure API endpoint (optional):
```bash
# Create .env file
echo "REACT_APP_API_URL=http://localhost:8000/api/v2" > .env
```

3. Start development server:
```bash
npm start
```

The app will run on http://localhost:3000

## Building for Production

```bash
npm run build
```

The build output will be in the `build` directory.

## Project Structure

```
src/
├── components/
│   └── Layout.tsx          # Main layout with navigation
├── contexts/
│   └── AuthContext.tsx     # Authentication context
├── pages/
│   ├── Dashboard.tsx       # Home page with file list
│   ├── Upload.tsx          # File upload page
│   ├── FileDetails.tsx     # Individual file details
│   └── SearchPage.tsx      # Search functionality
├── services/
│   └── api.ts              # API service layer
├── types/
│   └── index.ts            # TypeScript interfaces
├── App.tsx                 # Main app component
├── index.tsx               # App entry point
└── index.css               # Global styles
```

## Authentication

The app uses HTTP Basic Authentication. Users will be prompted to login when they first access the app. Credentials are stored in sessionStorage for the duration of the session.

## API Integration

The frontend communicates with the Music Analyzer V2 API at `/api/v2`. The proxy configuration in `package.json` forwards API requests to `http://localhost:8000` during development.

## Features in Detail

### Dashboard
- Display total files, storage size, and format statistics
- List recent files with basic information
- Quick actions for viewing and downloading files

### Upload
- Drag-and-drop or click to select files
- Support for multiple file uploads
- Progress tracking for each upload
- Supported formats: MP3, FLAC, WAV, M4A, OGG, OPUS, WMA

### File Details
- Complete file metadata display
- Audio transcription with language and confidence scores
- Lyrics search and display from multiple sources
- Export in multiple formats:
  - JSON: Complete data export
  - CSV: Spreadsheet format
  - Excel: Multi-sheet workbook
  - ZIP: Complete export with audio
  - TAR.GZ: Original audio files
  - Mono TAR.GZ: Processed mono files with metadata

### Search
- Two search modes:
  - Similar Content: Find music with similar transcriptions
  - Lyrics Search: Search by lyrics text
- Display search results with relevance scores
- Preview transcriptions and lyrics in results

## Environment Variables

- `REACT_APP_API_URL`: API base URL (defaults to `/api/v2`)

## Deployment

For production deployment:

1. Build the app:
```bash
npm run build
```

2. Serve the `build` directory with a web server (nginx, Apache, etc.)

3. Configure the web server to:
   - Serve the React app for all routes
   - Proxy `/api/v2/*` requests to the backend API