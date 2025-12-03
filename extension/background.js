/**
 * Background Service Worker for ChatGPT HTML to Word Converter
 * Handles cross-origin requests and extension lifecycle events
 */

// Extension installation event
chrome.runtime.onInstalled.addListener(() => {
  console.log('ChatGPT HTML to Word Converter extension installed');

  // Set default storage values
  chrome.storage.local.get(['api_url', 'default_format'], (result) => {
    if (!result.api_url) {
      chrome.storage.local.set({ api_url: 'http://localhost:8000' });
    }
    if (!result.default_format) {
      chrome.storage.local.set({ default_format: 'docx' });
    }
  });
});

// Handle messages from popup or content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // Handle conversion request (if using background to proxy requests)
  if (request.action === 'convert') {
    handleConversion(request.data)
      .then(response => sendResponse({ success: true, data: response }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Will respond asynchronously
  }

  // Handle API health check
  if (request.action === 'checkAPI') {
    checkAPIHealth(request.apiUrl)
      .then(isHealthy => sendResponse({ success: true, isHealthy }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  // Default response
  sendResponse({ success: false, error: 'Unknown action' });
});

/**
 * Handle HTML to Word/PDF conversion via background
 * This method can be used if you want to proxy requests through background
 */
async function handleConversion(data) {
  const { html, filename, format, apiUrl } = data;

  // Build form data
  const formData = new FormData();
  formData.append('html', html);
  if (filename) {
    formData.append('filename', filename);
  }
  formData.append('output_format', format);

  // Send request
  const response = await fetch(`${apiUrl}/convert`, {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail?.message || `HTTP ${response.status}`);
  }

  // Get blob
  const blob = await response.blob();

  // Convert blob to base64 for transfer
  const arrayBuffer = await blob.arrayBuffer();
  const uint8Array = new Uint8Array(arrayBuffer);
  const base64String = btoa(String.fromCharCode.apply(null, uint8Array));

  return {
    blob: base64String,
    filename: getFilenameFromResponse(response, filename, format)
  };
}

/**
 * Check if API is healthy
 */
async function checkAPIHealth(apiUrl) {
  try {
    const response = await fetch(`${apiUrl}/health`);
    return response.ok;
  } catch (error) {
    return false;
  }
}

/**
 * Extract filename from Content-Disposition header
 */
function getFilenameFromResponse(response, defaultFilename, format) {
  const contentDisposition = response.headers.get('Content-Disposition');
  if (contentDisposition) {
    const match = contentDisposition.match(/filename="([^"]+)"/);
    if (match) {
      return match[1];
    }
  }
  return `${defaultFilename || 'converted'}.${format}`;
}

/**
 * Handle browser action click (if needed for additional functionality)
 */
chrome.action.onClicked.addListener((tab) => {
  // This fires when the extension icon is clicked
  // Currently not used as we have a popup
  console.log('Extension icon clicked');
});

/**
 * Handle extension startup
 */
chrome.runtime.onStartup.addListener(() => {
  console.log('Extension started');
});
