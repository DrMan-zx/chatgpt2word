# ChatGPT to Word Converter

A browser extension and FastAPI backend that converts ChatGPT conversations (with KaTeX-rendered mathematical formulas) into editable Microsoft Word (.docx) documents.

## 🌟 Features

- ✅ Extracts mathematical formulas from ChatGPT's KaTeX rendering
- ✅ Converts to Word with **editable equations**
- ✅ One-click conversion from browser
- ✅ No login required, works with any ChatGPT conversation
- ✅ Docker support for easy deployment
- ✅ Open source and self-hosted

## 🏗️ Architecture

```
┌─────────────────────┐
│ Browser Extension   │  ← Extracts ChatGPT HTML
│ (Chrome/Firefox)    │  ← Calls API
└──────────┬──────────┘
           │ HTTP POST /convert
           ▼
┌─────────────────────┐
│ FastAPI Backend     │  ← Parses HTML, extracts LaTeX
│ (Python + Pandoc)   │  ← Converts to .docx
└──────────┬──────────┘
           │ Returns
           ▼
┌─────────────────────┐
│ Word Document       │  ← Downloadable .docx
│ (.docx file)        │  ← Editable equations
└─────────────────────┘
```

## 📦 Installation

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chatgpt2word
   ```

2. **Start the API server**
   ```bash
   cd api
   docker-compose up -d
   ```

3. **Install the Chrome extension**
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `extension/chrome` directory

4. **Done!** Click the extension icon on any ChatGPT page

### Option 2: Manual Installation

#### Backend Setup

1. **Install Python 3.11+**
   ```bash
   python --version
   ```

2. **Install Pandoc**
   - macOS: `brew install pandoc`
   - Ubuntu: `sudo apt-get install pandoc`
   - Windows: Download from [pandoc.org](https://pandoc.org/installing.html)

3. **Install Python dependencies**
   ```bash
   cd api
   pip install -r requirements.txt
   ```

4. **Run the API server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Extension Setup

Follow steps 3-4 from the Docker installation above.

## 🚀 Usage

1. **Open a ChatGPT conversation** with mathematical formulas
2. **Click the extension icon** in the Chrome toolbar
3. **Click "Convert to Word"**
4. **Save the downloaded .docx file**
5. **Open in Microsoft Word** - formulas are fully editable!

### Example

**Input** (ChatGPT HTML with KaTeX):
```html
<span class="katex">
  <annotation encoding="application/x-tex">
    \sin A + \sin B = 2 \sin\frac{A+B}{2}\cos\frac{A-B}{2}
  </annotation>
  ...
</span>
```

**Output** (Word document):
- Text content preserved
- Math formulas as **editable equations**

## 📁 Project Structure

```
chatgpt2word/
├── api/                          # FastAPI Backend
│   ├── main.py                   # API entry point
│   ├── html2word.py              # Conversion logic
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile               # Container config
│   └── docker-compose.yml       # Service setup
│
├── extension/                    # Browser Extension
│   ├── chrome/                   # Chrome extension
│   │   ├── manifest.json         # Extension config
│   │   ├── background.js         # Service worker
│   │   ├── content.js            # Content script
│   │   ├── popup/                # UI components
│   │   └── options.html          # Settings page
│   └── icons/                    # Extension icons
│
└── docs/                         # Documentation
    ├── API设计方案.md            # API spec
    ├── CLAUDE.md                 # Developer guide
    └── 目录结构说明.md           # Structure guide
```

## 🔧 API Reference

### Endpoint: `POST /convert`

Converts ChatGPT HTML to Word document.

**Request:**
```http
POST /convert
Content-Type: multipart/form-data

html: <Complete ChatGPT HTML with KaTeX formulas>
filename: <Optional custom filename without extension>
```

**Response (200):**
```
Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
Content-Disposition: attachment; filename="converted.docx"

[Binary .docx file]
```

**Error Response (4xx/5xx):**
```json
{
  "error": "ERROR_CODE",
  "message": "Human readable error message"
}
```

**Error Codes:**
- `400` - `invalid_request` - Missing required parameters
- `413` - `too_large` - HTML exceeds size limit
- `422` - `no_formulas` - No math formulas detected
- `500` - `conversion_failed` - Pandoc conversion failed

## 🧪 Testing

### Test the API directly
```bash
# Create a sample HTML file with KaTeX
cat > sample.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
  <p>Here is a formula:</p>
  <span class="katex">
    <annotation encoding="application/x-tex">\int_0^1 x^2 dx = 1/3</annotation>
  </span>
</body>
</html>
EOF

# Send to API
curl -X POST http://localhost:8000/convert \
  -F "html=@sample.html" \
  -F "filename=test" \
  --output result.docx
```

### Load Extension in Chrome
1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `extension/chrome` directory
5. Go to ChatGPT and test the extension

## 🐛 Troubleshooting

### Extension shows "Not a ChatGPT page"
- Make sure you're on `chat.openai.com` or `chatgpt.com`
- Refresh the page and try again

### API connection failed
- Check if API server is running on port 8000
- Verify the API URL in extension settings
- Check browser console for errors

### Conversion failed
- Ensure HTML contains KaTeX formulas (look for `<annotation encoding="application/x-tex">`)
- Check API logs for error details
- Verify Pandoc is installed correctly

### No editable formulas in Word
- This is expected for complex formulas
- Simple formulas will be editable
- Formulas are preserved as text at minimum

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- [Pandoc](https://pandoc.org/) - Document conversion
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- KaTeX - Mathematical typesetting

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the documentation in `docs/`
- Review the API specification
