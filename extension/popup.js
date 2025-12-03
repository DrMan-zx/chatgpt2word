// DOM Elements
const htmlInput = document.getElementById('html-input');
const filenameInput = document.getElementById('filename-input');
const formatSelect = document.getElementById('format-select');
const apiUrlInput = document.getElementById('api-url');
const convertBtn = document.getElementById('convert-btn');
const statusDiv = document.getElementById('status');
const statusIcon = document.getElementById('status-icon');
const statusText = document.getElementById('status-text');
const progressDiv = document.getElementById('progress');
const errorDiv = document.getElementById('error');
const errorText = document.getElementById('error-text');

// Configuration
const STORAGE_KEYS = {
  API_URL: 'converter_api_url',
  FILENAME: 'converter_filename',
  FORMAT: 'converter_format'
};

const DEFAULTS = {
  API_URL: 'http://localhost:8000',
  FORMAT: 'docx'
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
  setupEventListeners();
});

/**
 * Load settings from chrome.storage
 */
function loadSettings() {
  chrome.storage.local.get([STORAGE_KEYS.API_URL, STORAGE_KEYS.FILENAME, STORAGE_KEYS.FORMAT], (result) => {
    if (result[STORAGE_KEYS.API_URL]) {
      apiUrlInput.value = result[STORAGE_KEYS.API_URL];
    }
    if (result[STORAGE_KEYS.FILENAME]) {
      filenameInput.value = result[STORAGE_KEYS.FILENAME];
    }
    if (result[STORAGE_KEYS.FORMAT]) {
      formatSelect.value = result[STORAGE_KEYS.FORMAT];
    }
  });
}

/**
 * Save settings to chrome.storage
 */
function saveSettings() {
  chrome.storage.local.set({
    [STORAGE_KEYS.API_URL]: apiUrlInput.value.trim(),
    [STORAGE_KEYS.FILENAME]: filenameInput.value.trim(),
    [STORAGE_KEYS.FORMAT]: formatSelect.value
  });
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // Save settings on change
  apiUrlInput.addEventListener('change', saveSettings);
  filenameInput.addEventListener('change', saveSettings);
  formatSelect.addEventListener('change', saveSettings);

  // Convert button
  convertBtn.addEventListener('click', handleConvert);

  // Enter key to trigger conversion
  htmlInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleConvert();
    }
  });

  // Auto-save on input
  filenameInput.addEventListener('input', saveSettings);
}

/**
 * Handle convert button click
 */
async function handleConvert() {
  try {
    // Validate inputs
    const htmlContent = htmlInput.value.trim();
    const filename = filenameInput.value.trim();
    const format = formatSelect.value;
    const apiUrl = apiUrlInput.value.trim();

    if (!htmlContent) {
      showError('请输入 HTML 内容');
      return;
    }

    if (!apiUrl) {
      showError('请输入 API 地址');
      return;
    }

    // Validate HTML content
    if (!validateHTML(htmlContent)) {
      showError('请输入有效的 HTML 内容');
      return;
    }

    // Save settings
    saveSettings();

    // Show loading state
    setLoadingState(true);
    hideError();

    // Convert
    await convertHTML(htmlContent, filename, format, apiUrl);

  } catch (error) {
    showError(error.message);
    console.error('Conversion error:', error);
  } finally {
    setLoadingState(false);
  }
}

/**
 * Validate HTML content
 */
function validateHTML(html) {
  // Basic validation - check if it contains HTML tags and has content
  return html.length > 0 && html.includes('<') && html.includes('>');
}

/**
 * Convert HTML to Word/PDF
 */
async function convertHTML(html, filename, format, apiUrl) {
  try {
    updateStatus('正在连接 API...', 'loading');

    // Build form data
    const formData = new FormData();
    formData.append('html', html);
    if (filename) {
      formData.append('filename', filename);
    }
    formData.append('output_format', format);

    // Build API URL
    const url = new URL('/convert', apiUrl);
    updateStatus('正在发送请求...', 'loading');

    // Send request
    const response = await fetch(url.toString(), {
      method: 'POST',
      body: formData
    });

    // Check response
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage = errorData.detail?.message || errorData.message || `HTTP ${response.status}`;
      throw new Error(errorMessage);
    }

    updateStatus('正在下载文件...', 'loading');

    // Get blob
    const blob = await response.blob();

    // Get filename from Content-Disposition header
    let downloadFilename = filename || 'converted';
    const contentDisposition = response.headers.get('Content-Disposition');
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="([^"]+)"/);
      if (match) {
        downloadFilename = match[1];
      }
    } else {
      // Add extension if not present
      if (!downloadFilename.endsWith(`.${format}`)) {
        downloadFilename += `.${format}`;
      }
    }

    // Download file
    downloadBlob(blob, downloadFilename);

    // Show success
    updateStatus('转换成功！文件已下载', 'success');

  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('无法连接到 API 服务，请检查 API 地址是否正确并确保服务正在运行');
    }
    throw error;
  }
}

/**
 * Download blob as file
 */
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Update status
 */
function updateStatus(message, type) {
  statusText.textContent = message;
  statusDiv.className = `status ${type || ''}`;
}

/**
 * Show error message
 */
function showError(message) {
  errorText.textContent = message;
  errorDiv.classList.remove('hidden');
  updateStatus('发生错误', 'error');
}

/**
 * Hide error message
 */
function hideError() {
  errorDiv.classList.add('hidden');
}

/**
 * Set loading state
 */
function setLoadingState(isLoading) {
  if (isLoading) {
    convertBtn.disabled = true;
    convertBtn.classList.add('loading');
    convertBtn.querySelector('span').textContent = '转换中...';
    progressDiv.classList.remove('hidden');
  } else {
    convertBtn.disabled = false;
    convertBtn.classList.remove('loading');
    convertBtn.querySelector('span').textContent = '开始转换';
    progressDiv.classList.add('hidden');
  }
}
