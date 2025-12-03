# ChatGPT to Word Converter API Specifications

This document defines the shared conventions between the browser extension and the API backend. Both components must adhere to these specifications to ensure compatibility.

## 🚀 Current Implementation Status

**API Version:** 1.0.0 ✅ **Fully Implemented - Now with Universal HTML Support!**

## Core Features

### ✅ HTML Processing Engine
- **Universal HTML Support**: Processes any HTML content, with or without math formulas
- **KaTeX Formula Conversion**: Converts complex KaTeX math formulas to standard LaTeX format (when present)
- **Smart Table Restructuring**: Optimizes ChatGPT-specific table containers
- **Code Block Optimization**: Simplifies nested code structures
- **Emoji Preservation**: Retains original Unicode emoji characters
- **Data Attribute Cleanup**: Removes ChatGPT-specific `data-*` attributes

### ✅ Output Formats
- **DOCX**: Full Word document support with optional math formulas
- **PDF**: High-quality PDF output with multiple engine support (WeasyPrint, pdfLaTeX, XeLaTeX)

### ✅ Error Handling
- Complete validation with detailed error codes
- User-friendly error messages
- Timeout protection (30 seconds)
- Size limitations (50MB max)

## API Endpoints

### Primary Conversion Endpoint
**URL:** `POST /convert`
**Content-Type:** `multipart/form-data`
**Character Encoding:** UTF-8

### Health Check Endpoints
- `GET /` - Service information and status
- `GET /health` - Health check

## Request Format

### Required Fields
- `html` (string) - Complete HTML content (KaTeX formulas optional)

### Optional Fields
- `filename` (string) - Custom filename without extension
- `output_format` (string) - Output format: "docx" (default) or "pdf"

### Example Request
```http
POST /convert HTTP/1.1
Content-Type: multipart/form-data

html=<!DOCTYPE html>...</html>
filename=第3章_数学公式整理
output_format=docx
```

## Success Response

**Status Code:** `200 OK`

### For DOCX Output
**Headers:**
- `Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- `Content-Disposition: attachment; filename="{filename}.docx"`

**Body:** Binary .docx file stream

### For PDF Output
**Headers:**
- `Content-Type: application/pdf`
- `Content-Disposition: attachment; filename="{filename}.pdf"`

**Body:** Binary .pdf file stream

### Health Check Responses
**GET /** Response:
```json
{
  "service": "ChatGPT to Word Converter",
  "version": "1.0.0",
  "status": "running"
}
```

**GET /health** Response:
```json
{
  "status": "healthy"
}
```

## Error Response Format

**Status Code:** 4xx (client error) or 5xx (server error)
**Content-Type:** `application/json`

**Format:**
```json
{
  "error": "ERROR_CODE",
  "message": "Human readable error message"
}
```

## Error Codes

### 4xx Client Errors

#### 400 - invalid_request
**Meaning:** Missing required parameters or invalid request format
**When it occurs:**
- `html` parameter is missing
- Request body is malformed
- Content-Type is not multipart/form-data

**Extension should:**
- Show user a message to check the page content
- Retry if this seems like a temporary error

#### 400 - invalid_format
**Meaning:** Invalid output format specified
**When it occurs:**
- `output_format` is not "docx" or "pdf"
- Output format parameter contains unexpected values

**Extension should:**
- Show user a message to select a valid format
- Provide format selection in UI

#### 413 - too_large
**Meaning:** HTML content exceeds size limit
**When it occurs:**
- HTML size > 50MB
- File too large to process

**Extension should:**
- Inform user to reduce content size
- Suggest converting shorter conversations

#### 400 - invalid_html
**Meaning:** Invalid HTML format provided
**When it occurs:**
- HTML doesn't contain basic HTML tags
- Content is not valid HTML format
- String content is not properly formatted

**Extension should:**
- Show message: "Please enter valid HTML content."
- Suggest copying content from the original page
- Check that the content was copied correctly

### 5xx Server Errors

#### 500 - conversion_failed
**Meaning:** Pandoc conversion process failed
**When it occurs:**
- Pandoc is not installed
- HTML parsing failed
- Temporary file creation failed
- Pandoc error during conversion

**Extension should:**
- Show error message with details
- Suggest checking API server logs
- Offer to retry the conversion

#### 500 - conversion_timeout
**Meaning:** Conversion took too long (>30 seconds)
**When it occurs:**
- HTML is very large or complex
- System is under high load
- Pandoc is hanging

**Extension should:**
- Inform user that conversion timed out
- Suggest trying with a smaller selection

#### 500 - internal_error
**Meaning:** Unexpected server error
**When it occurs:**
- Unhandled exception in API code
- System resource issues
- Unknown error conditions

**Extension should:**
- Show generic error message
- Log error details for debugging
- Suggest retrying later

## Content Type Mappings

The API returns different Content-Types based on `output_format`:
- For "docx": `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- For "pdf": `application/pdf`

The extension should use this to:
- Save the file with the appropriate extension (`.docx` or `.pdf`)
- Open with the appropriate application (Word for docx, PDF viewer for pdf)
- Handle as a binary download

## File Naming

**If `filename` parameter is provided:**
- Use as the base name (without extension)
- Sanitize to remove: `\ / : * ? " < > |`
- Limit to 100 characters
- Add extension based on `output_format` (default: `.docx`)

**If `filename` is not provided:**
- Use default name: "converted.docx" or "converted.pdf"
- Extension based on `output_format` parameter

**Examples:**
- Input: "Chapter 1 - Math Formulas" (output_format=docx)
- Output: "Chapter 1 - Math Formulas.docx"

- Input: "Test/Page" (invalid, output_format=pdf)
- Output: "Test_Page.pdf"

## Validation Rules

**HTML Validation:**
- Must contain basic HTML tags (< and >)
- Must be valid HTML (can be parsed by BeautifulSoup)
- Maximum size: 50MB
- KaTeX formulas are optional but supported when present

**Filename Validation:**
- Optional: can be empty or omitted
- If provided, must be string
- Will be sanitized automatically

**Output Format Validation:**
- Optional: can be "docx" or "pdf"
- If omitted, defaults to "docx"
- Case-sensitive: "DOCX" will be rejected

## Versioning

**Current API Version:** 1.0.0

**Backward Compatibility:**
- Existing extensions will continue to work
- New optional parameters can be added
- Existing required parameters won't change
- Error codes won't be removed
- Success response format won't change

**Version Header:**
The API includes version information in responses:
```json
{
  "service": "ChatGPT to Word Converter",
  "version": "1.0.0",
  "status": "running"
}
```

## Rate Limiting

**Not implemented in version 1.0.0**
- Future versions may add rate limiting (429 errors)
- Extensions should be prepared to handle 429
- Implement exponential backoff for retries

## Caching

**Not implemented in version 1.0.0**
- Future versions may cache results
- Cache key will be based on HTML content hash
- Cache will be transparent to the extension

## 🔧 Extension Development Guide

### Best Practices for Extension Developers

1. **Always show progress**
   - Disable convert button during processing
   - Show loading indicator with time estimates
   - Provide clear success/error messages

2. **Handle all error codes**
   - Implement handlers for all documented error codes
   - Display user-friendly messages based on error types
   - Log technical details for debugging purposes

3. **Smart validation**
   - Check if page contains valid HTML content
   - Validate file size limits (50MB)
   - Sanitize user-provided filenames
   - KaTeX formulas are automatically detected and processed when present

4. **Robust error handling**
   - Only retry on temporary errors (500, network issues)
   - Don't retry on validation errors (400, 413, 422)
   - Implement exponential backoff for retries

5. **Enhanced user experience**
   - Provide custom filename option with preview
   - Show word count and processing time estimates
   - Save API URL and preferences in extension storage
   - Support both DOCX and PDF format selection

### Implementation Tips

**HTML Content Validation:**
```javascript
// Check for valid HTML content before conversion
const hasValidHTML = htmlContent.length > 0 && htmlContent.includes('<') && htmlContent.includes('>');
if (!hasValidHTML) {
    alert('Please enter valid HTML content.');
    return;
}
```

**Progress Management:**
```javascript
// Show realistic time estimates
function showProgress() {
    const wordCount = document.body.innerText.length;
    const estimatedTime = Math.max(3, Math.ceil(wordCount / 1000));
    showLoader(`Converting... (estimated ${estimatedTime} seconds)`);
}
```

**Error Recovery:**
```javascript
// Smart retry logic
async function convertWithRetry(html, maxRetries = 2) {
    for (let i = 0; i <= maxRetries; i++) {
        try {
            return await convert(html);
        } catch (error) {
            if (i === maxRetries || !isRetryableError(error)) {
                throw error;
            }
            await delay(1000 * Math.pow(2, i)); // Exponential backoff
        }
    }
}
```

## 🧪 Testing Guide

### Test Environment Setup
- API server running on `http://localhost:8000`
- Test files located in `/shared/` directory
- Use ChatGPT conversations with mathematical formulas

### Valid Test Cases

**1. Standard Conversion**
- Load ChatGPT page with mathematical formulas
- Extract complete HTML content
- Convert to both DOCX and PDF formats
- Verify file downloads with correct naming

**2. Conversion Without Math Formulas**
- Test simple HTML content without KaTeX formulas
- Verify conversion works for regular text, tables, and formatting
- Test HTML content from various sources (not just ChatGPT)

**3. Custom Features**
- Test custom filename input
- Test special characters in filenames
- Test large conversations (within 50MB limit)
- Test emoji preservation in output

**4. Formula Validation (Optional)**
- Test various math formula types:
  - Inline formulas: `$x = \frac{1}{2}$`
  - Display formulas: `$$E = mc^2$$`
  - Complex expressions with Greek letters
  - Multi-line equations

### Error Testing

**4. Input Validation**
- Empty HTML string → HTTP 400
- Invalid HTML format (no HTML tags) → HTTP 400
- HTML > 50MB → HTTP 413
- Invalid output format → HTTP 400

**5. Network Testing**
- Invalid API URL
- API server offline
- Connection timeout scenarios

### Automated Testing
Use the provided test files:
- `shared/chat.txt` - Basic conversation with formulas
- `shared/chat2.txt` - Complex mathematical content

**Sample Test Script:**
```bash
# Test API health
curl http://localhost:8000/health

# Test valid conversion
curl -X POST http://localhost:8000/convert \
  -F "html=@shared/chat2.txt" \
  -F "filename=test_docx" \
  -o result.docx

# Test error conditions
curl -X POST http://localhost:8000/convert \
  -F "html=Invalid content without HTML tags" \
  # Should return 400 error

# Test conversion without math formulas (should work)
curl -X POST http://localhost:8000/convert \
  -F "html=<h1>Simple Test</h1><p>No math formulas here.</p>" \
  -F "filename=simple_test" \
  -o result.docx
```

## ✅ Implementation Status

### Completed Features (v1.0.0)
- ✅ **Complete API Implementation**: All core features fully functional
- ✅ **Math Formula Processing**: KaTeX to LaTeX conversion with Pandoc integration
- ✅ **Multi-format Output**: DOCX and PDF generation
- ✅ **Smart HTML Processing**: Optimized for ChatGPT export format
- ✅ **Comprehensive Error Handling**: All error codes implemented
- ✅ **Health Monitoring**: Service status endpoints
- ✅ **Docker Support**: Containerized deployment ready

### Known Limitations
- **Math Formula Display**: May appear as LaTeX text in Word 2013 (Word 2016+ recommended)
- **Concurrent Processing**: Single-threaded (suitable for <5 concurrent requests)
- **Network Dependency**: Requires internet connection for optional math rendering
- **Source Optimization**: Optimized for ChatGPT exports but works with any HTML content

### Next Version (Planned)
The following features are planned for future versions while maintaining backward compatibility:

1. **Performance Enhancements**
   - Process pool for concurrent processing (20+ requests)
   - Result caching for repeated conversions
   - Request queuing for high load scenarios

2. **Advanced Output Options**
   - Math rendering as images (for older Word versions)
   - Custom styling and formatting options
   - Batch conversion support

3. **Integration Features**
   - API authentication and rate limiting
   - Usage analytics and monitoring
   - Cloud storage integration

### Backward Compatibility Guarantee
- ✅ **All existing extensions will continue to work**
- ✅ **API interface will remain stable**
- ✅ **New features added as optional parameters only**
- ✅ **Error codes will not be removed**
