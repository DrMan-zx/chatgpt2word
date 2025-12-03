# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository is a **monorepo** containing a browser extension and FastAPI backend service that converts ChatGPT conversations (with KaTeX-rendered mathematical formulas) into editable Microsoft Word (.docx) documents. The browser extension extracts HTML from ChatGPT pages and sends it to the API, which uses Pandoc to generate Word documents with editable equations.

## High-Level Architecture

```
┌─────────────────────┐
│ Browser Extension   │  ← Extracts ChatGPT HTML
│ (Chrome/Firefox)    │  ← Calls API
└──────────┬──────────┘
           │ HTTP POST /convert
           ▼
┌─────────────────────┐
│ FastAPI Backend     │  ← Parses HTML, extracts LaTeX
│ (api/main.py)       │  ← Converts via Pandoc
└──────────┬──────────┘
           │ Returns
           ▼
┌─────────────────────┐
│ Word Document       │  ← Downloadable .docx
│ (.docx file)        │  ← Editable equations
└─────────────────────┘
```

## Repository Structure

```
chatgpt2word/
├── api/                          # FastAPI Backend Service
│   ├── main.py                   # FastAPI application entry point
│   ├── html2word.py              # Core conversion logic (from KaTeX HTML)
│   ├── handlers/                 # Request handlers
│   ├── services/                 # Business logic services
│   ├── utils/                    # Utility functions
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile               # Container build definition
│   └── docker-compose.yml       # Service orchestration
│
├── extension/                    # Browser Extension
│   ├── chrome/                   # Chrome extension (Manifest V3)
│   │   ├── manifest.json         # Extension manifest
│   │   ├── background.js         # Service worker
│   │   ├── content.js            # Injected into ChatGPT pages
│   │   ├── popup/                # Extension popup UI
│   │   └── icons/                # Extension icons
│   ├── firefox/                  # Firefox version (optional)
│   └── shared/                   # Shared extension code
│
├── shared/                       # Shared code and conventions
│   └── README.md                 # API format and error code conventions
│
├── docs/                         # Project Documentation
│   ├── API设计方案.md            # API design specification
│   ├── CLAUDE.md                 # This file
│   ├── 目录结构说明.md           # Directory structure guide
│   └── examples/                 # Sample files
│
└── tests/                        # Test Suites (to be created)
    ├── api/                      # API tests
    └── extension/                # Extension tests
```

## Core Components

### API Backend (Python/FastAPI)
**Location**: `api/`
- **Purpose**: Receives ChatGPT HTML, extracts LaTeX formulas, converts to Word
- **Key Algorithm**: `html2word.py` - Parses KaTeX `<annotation encoding="application/x-tex">` tags, converts to markdown, uses Pandoc for .docx generation
- **API Endpoint**: `POST /convert` (multipart/form-data)
- **Dependencies**: `beautifulsoup4`, `lxml`, `fastapi`, `pandoc`

### Browser Extension (JavaScript)
**Location**: `extension/chrome/`
- **Purpose**: Extracts ChatGPT conversation HTML, sends to API, downloads result
- **Components**:
  - `content.js` - Injects into ChatGPT to extract conversation HTML
  - `background.js` - Handles API communication and file downloads
  - `popup/` - User interface for configuration and manual conversion

## Development Commands

### API Development
```bash
# Install Python dependencies
cd api
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Test the conversion endpoint
curl -X POST http://localhost:8000/convert \
  -F "html=@sample.html" \
  -F "filename=test" \
  --output result.docx
```

### Building Docker Image
```bash
# Build API image
cd api
docker build -t chatgpt2word-api .

# Run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Extension Development
```bash
# Chrome: Load unpacked extension
# 1. Open chrome://extensions/
# 2. Enable "Developer mode"
# 3. Click "Load unpacked"
# 4. Select extension/chrome directory

# Firefox: Use web-ext
npm install -g web-ext
cd extension/firefox
web-ext run
```

## Key Technical Details

### Conversion Pipeline
1. **HTML Parsing** - BeautifulSoup parses ChatGPT HTML export
2. **LaTeX Extraction** - Extracts formulas from `<annotation encoding="application/x-tex">` tags
3. **Markdown Generation** - Strips HTML, replaces KaTeX with `$$...$$` formulas
4. **Pandoc Conversion** - Converts markdown to .docx with editable equations

### API Interface (Stable Contract)
```
POST /convert
Content-Type: multipart/form-data

Request:
  - html: Complete ChatGPT HTML with KaTeX formulas
  - filename: Optional custom filename (without extension)

Response:
  - 200: Binary .docx file
  - 4xx/5xx: JSON error { "error": "CODE", "message": "..." }
```

### Extension Integration Points
- **Content Script**: Monitors ChatGPT DOM for new messages
- **API Communication**: Uses fetch() to call `/convert` endpoint
- **File Download**: Creates blob URL and triggers download
- **UI**: Popup allows manual conversion and settings

## Current Development Status

✅ **Completed**:
- API design specification (docs/API设计方案.md)
- Core conversion logic (api/html2word.py)
- Docker configuration (api/Dockerfile, docker-compose.yml)
- Project directory structure

🔄 **In Progress**:
- FastAPI main.py and routing structure
- Chrome extension manifest and core files

📋 **Planned**:
- Content script for ChatGPT HTML extraction
- Extension popup UI
- API request/response handling
- Error handling and validation
- Unit tests (api/ and tests/)
- Deployment documentation

## Key Dependencies

### API Backend
- **Python 3.11+** - Runtime environment
- **FastAPI** - Web framework
- **BeautifulSoup4** - HTML parsing
- **lxml** - XML/HTML processor
- **Pandoc** - Document conversion (installed in Docker image)

### Browser Extension
- **Manifest V3** - Chrome extension standard
- **Vanilla JavaScript** - No framework dependencies
- **Chrome Extension APIs** - tabs, storage, downloads

## Important Files

- **`api/html2word.py`** - Core conversion algorithm (KaTeX → LaTeX → Markdown → Word)
- **`api/main.py`** - FastAPI application (to be created)
- **`extension/chrome/manifest.json`** - Extension configuration (to be created)
- **`docs/API设计方案.md`** - Complete API specification
- **`api/Dockerfile`** - Container build instructions
- **`api/docker-compose.yml`** - Local development setup

## Working on This Project

**When adding new features**:
1. Check if changes affect API contract (docs/API设计方案.md)
2. Update both API and extension if needed
3. Add tests in `tests/` directory
4. Update documentation in `docs/`

**When fixing bugs**:
1. Identify affected component (API vs extension)
2. Update `api/html2word.py` for conversion issues
3. Update extension files for extraction/UI issues
4. Add regression test

**When modifying API**:
- Ensure backward compatibility for existing extensions
- Update error codes in `shared/README.md`
- Test with sample HTML from `docs/examples/`
