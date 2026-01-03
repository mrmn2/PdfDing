// function for getting the signature
async function get_remote_signatures(signature_url) {
  try {
    const response = await fetch(signature_url);
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }

    const result = await response.json();
    localStorage.setItem("previous_pdfjs.signature", JSON.stringify(result));
    localStorage.setItem("pdfjs.signature", JSON.stringify(result));
  } catch (error) {
    console.error(error.message);
  }
}

// function for updating the remote page
function update_remote_page(pdf_id, update_url, csrf_token) {
  if (PDFViewerApplication.pdfViewer.currentPageNumber != page_number) {
    page_number = PDFViewerApplication.pdfViewer.currentPageNumber;
    set_current_page(page_number, pdf_id, update_url, csrf_token);
  }
}

// function for setting the current page
function set_current_page(current_page, pdf_id, update_url, csrf_token) {
  var form_data = new FormData();
  form_data.append('pdf_id', pdf_id);
  form_data.append('current_page', current_page);

  fetch(update_url, {
    method: "POST",
    body: form_data,
    headers: {
      'X-CSRFToken': csrf_token,
    },
  });
}

// function for updating the remote signatures
async function update_remote_signatures(signature_url, csrf_token) {
  const previous_signatures = localStorage.getItem("previous_pdfjs.signature");
  const current_signatures = localStorage.getItem("pdfjs.signature");

  // check if signatures were updated by pdfjs
  if (current_signatures != previous_signatures) {
    const status_code = await set_remote_signatures(current_signatures, previous_signatures, signature_url, csrf_token);

    if (status_code === 201) {
      // refresh signatures in local storage
      get_remote_signatures(signature_url);
    }
  }
}

// function for setting signatures
async function set_remote_signatures(current_signatures, previous_signatures, signature_url, csrf_token) {
  var form_data = new FormData();
  form_data.append('current_signatures', current_signatures);
  form_data.append('previous_signatures', previous_signatures);

  const response = await fetch(signature_url, {
    method: "POST",
    body: form_data,
    headers: {
      'X-CSRFToken': csrf_token,
    },
  });

  return response.status
}

// send file via the fetch api to the backend
function send_pdf_file(file, pdf_id, update_url, csrf_token) {
  var form_data = new FormData();
  form_data.append('updated_pdf', file);
  form_data.append('pdf_id', pdf_id);

  fetch(update_url, {
    method: "POST",
    body: form_data,
    headers: {
      'X-CSRFToken': csrf_token,
    },
  });
}

// function for updating the pdf file in the backend
async function update_pdf(pdf_id, update_url, csrf_token, tab_title) {
  if (PDFViewerApplication._saveInProgress) {
    return;
  }
  PDFViewerApplication._saveInProgress = true;
  await PDFViewerApplication.pdfScriptingManager.dispatchWillSave();

  try {
    const data = await PDFViewerApplication.pdfDocument.saveDocument();
    const updated_pdf = new Blob([data], {type: "application/pdf"});
    send_pdf_file(updated_pdf, pdf_id, update_url, csrf_token);
    PDFViewerApplication._hasAnnotationEditors = false;
    // removes "*" from the tab title in order to signal that the file was successfully saved
    PDFViewerApplication.setTitle(tab_title);
  } catch (reason) {
    console.error(`Error when saving the document: ${reason.message}`);
  } finally {
    await PDFViewerApplication.pdfScriptingManager.dispatchDidSave();
    PDFViewerApplication._saveInProgress = false;
  }
}

// function for requesting a wake lock
const requestWakeLock = async () => {
  try {
    wakeLock = await navigator.wakeLock.request();
    wakeLock.addEventListener('release', () => {
      console.log('Screen Wake Lock released:', wakeLock.released);
    });
  } catch (err) {
    console.error(`${err.name}, ${err.message}`);
  }
};

// AI functionality
let selectedText = '';
let aiButton = null;

// Initialize AI features when the document is loaded
function initializeAIFeatures() {
  console.log('Initializing AI features...');
  
  // Get the AI button
  aiButton = document.getElementById('aiButton');
  console.log('AI Button:', aiButton);
  
  if (!aiButton) {
    console.log('AI button not found in DOM');
    return;
  }

  // Add event listeners for text selection
  // Try multiple event types to ensure we catch selection changes
  document.addEventListener('mouseup', handleTextSelection);
  document.addEventListener('keyup', handleTextSelection);
  document.addEventListener('selectionchange', handleTextSelection);
  
  // Also check for touch events on mobile
  document.addEventListener('touchend', handleTextSelection);

  // Add event listener for the AI button
  aiButton.addEventListener('click', handleAIButtonClick);
  console.log('AI features initialized successfully');
}

// Handle text selection
function handleTextSelection() {
  // Try multiple methods to get selected text
  let text = '';
  
  // Method 1: Standard window selection (fallback)
  const selection = window.getSelection();
  if (selection && selection.toString) {
    text = selection.toString().trim();
  }
  
  // Method 2: Try to get text from PDF.js text layer if available
  if (!text && typeof PDFViewerApplication !== 'undefined' && 
      PDFViewerApplication.pdfViewer && PDFViewerApplication.pdfViewer.currentPageNumber) {
    // Look for selected text in the PDF text layer
    const textLayers = document.querySelectorAll('.textLayer');
    for (let layer of textLayers) {
      const selectedElements = layer.querySelectorAll('.highlight.selected');
      if (selectedElements.length > 0) {
        // Try to get text content from selected elements
        for (let element of selectedElements) {
          if (element.textContent) {
            text += element.textContent + ' ';
          }
        }
        text = text.trim();
      }
    }
    
    console.log('PDF.js is loaded, current page:', PDFViewerApplication.pdfViewer.currentPageNumber);
  }
  
  // Method 3: Try to get text directly from highlighted elements
  if (!text) {
    const highlightedElements = document.querySelectorAll('.highlight.selected');
    if (highlightedElements.length > 0) {
      for (let element of highlightedElements) {
        if (element.textContent) {
          text += element.textContent + ' ';
        }
      }
      text = text.trim();
    }
  }
  
  // Method 4: Try to capture text layer content directly (PDF.js specific)
  if (!text) {
    // Try to get text from the current page's text layer
    const currentPage = typeof PDFViewerApplication !== 'undefined' ? 
      PDFViewerApplication.pdfViewer.currentPageNumber : null;
    
    if (currentPage) {
      // Look for text layer of current page
      const pageDiv = document.querySelector(`#pageContainer${currentPage} .textLayer`);
      if (pageDiv) {
        // Try to get selected text from the page div
        const range = selection.getRangeAt(0);
        if (range && range.toString().trim()) {
          text = range.toString().trim();
        }
      }
    }
  }
  
  selectedText = text;
  
  console.log('Selection object:', selection);
  console.log('Selected text:', selectedText);
  console.log('Selection length:', selectedText.length);
  
  // Show/hide AI button based on text selection
  if (aiButton) {
    if (selectedText.length > 0) {
      aiButton.style.display = 'inline-block';
      console.log('Showing AI button');
    } else {
      aiButton.style.display = 'none';
      console.log('Hiding AI button');
    }
  }
}

// Handle AI button click
function handleAIButtonClick() {
  console.log('AI button clicked');
  console.log('Current selected text:', selectedText);
  
  if (!selectedText) {
    console.log('No selected text found');
    alert('Please select some text first.');
    return;
  }
  
  // Show a prompt for the user's question
  const question = prompt('Ask a question about the selected text:', '');
  console.log('User question:', question);
  
  if (!question) {
    console.log('No question provided');
    return;
  }
  
  // Create a modal dialog for the AI response
  showAIResponseModal('Asking AI...', true, question, selectedText);
  
  // Send request to backend
  askAIAboutText(selectedText, question);
}

// Send AI request to backend
async function askAIAboutText(text, question) {
  try {
    console.log('Sending AI request with:');
    console.log('Text:', text);
    console.log('Question:', question);
    
    // Get the PDF ID from the global variable set in the template
    const pdfId = window.pdf_id || window.shared_pdf_id;
    console.log('PDF ID:', pdfId);
    
    if (!pdfId) {
      throw new Error('PDF ID not found');
    }
    
    // Create form data
    const formData = new FormData();
    formData.append('selected_text', text);
    formData.append('question', question);
    
    // Get CSRF token - try multiple methods
    let csrfToken = null;
    
    // Method 1: Look for CSRF token in meta tag
    const csrfMetaTag = document.querySelector('meta[name="csrf-token"]');
    if (csrfMetaTag) {
      csrfToken = csrfMetaTag.getAttribute('content');
      console.log('CSRF Token from meta tag:', csrfToken ? 'Found' : 'Not found');
    }
    
    // Method 2: Look for CSRF token in hidden input
    if (!csrfToken) {
      const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
      if (csrfInput) {
        csrfToken = csrfInput.value;
        console.log('CSRF Token from input:', csrfToken ? 'Found' : 'Not found');
      }
    }
    
    // Method 3: Look for CSRF token in cookies
    if (!csrfToken) {
      const cookies = document.cookie.split(';');
      for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
          csrfToken = value;
          console.log('CSRF Token from cookie:', csrfToken ? 'Found' : 'Not found');
          break;
        }
      }
    }
    
    if (!csrfToken) {
      throw new Error('CSRF token not found');
    }
    
    // Make request to backend
    const url = `/pdf/ai/ask_about_text/${pdfId}`;
    console.log('Sending request to:', url);
    
    // Log the form data
    for (let pair of formData.entries()) {
      console.log(pair[0] + ': ' + pair[1]);
    }
    
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': csrfToken
      }
    });
    
    console.log('Response status:', response.status);
    console.log('Response headers:', [...response.headers.entries()]);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.log('Error response body:', errorText);
      throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    
    const data = await response.json();
    console.log('Response data:', data);
    
    if (data.error) {
      throw new Error(data.error);
    }
    
    showAIResponseModal(data.answer, false, question, text);
    
  } catch (error) {
    console.error('Error asking AI:', error);
    showAIResponseModal('Error: ' + error.message, false, question);
  }
}

// Current question and answer for saving
let currentQuestion = '';
let currentAnswer = '';
let currentSelectedText = '';

// Show AI response modal
function showAIResponseModal(content, isLoading, question = '', selectedText = '') {
  // Remove any existing modal
  const existingModal = document.getElementById('aiResponseModal');
  if (existingModal) {
    existingModal.remove();
  }
  
  // Store current question and answer
  currentQuestion = question;
  currentAnswer = isLoading ? '' : content;
  currentSelectedText = selectedText;
  
  // Create modal HTML
  const modalHTML = `
    <div id="aiResponseModal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); z-index: 10000; display: flex; justify-content: center; align-items: center;">
      <div style="background: white; border-radius: 8px; padding: 20px; max-width: 80%; max-height: 80%; overflow: auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
          <h3 style="margin: 0; color: #333;">AI Assistant</h3>
          <button id="closeAIResponseModal" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #333;">×</button>
        </div>
        <div id="aiResponseContent" style="white-space: pre-wrap; max-height: 60vh; overflow-y: auto; color: #333; font-family: Arial, sans-serif; line-height: 1.5;">
          ${isLoading ? '<div style="text-align: center;"><div style="border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 0 auto;"></div><p style="text-align: center; margin-top: 10px; color: #333;">Thinking...</p></div>' : content}
        </div>
        <div style="margin-top: 15px; text-align: right;">
          <button id="saveAIResponse" style="background-color: #27ae60; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-right: 10px;">Save</button>
          <button id="copyAIResponse" style="background-color: #3498db; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-right: 10px;">Copy</button>
          <button id="closeAIResponse" style="background-color: #7f8c8d; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Close</button>
        </div>
      </div>
    </div>
  `;
  
  // Add CSS for spinner animation
  const style = document.createElement('style');
  style.innerHTML = `
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(style);
  
  // Add modal to document
  document.body.insertAdjacentHTML('beforeend', modalHTML);
  
  // Add event listeners
  document.getElementById('closeAIResponseModal').addEventListener('click', closeAIResponseModal);
  document.getElementById('closeAIResponse').addEventListener('click', closeAIResponseModal);
  document.getElementById('copyAIResponse').addEventListener('click', copyAIResponse);
  document.getElementById('saveAIResponse').addEventListener('click', saveAIResponse);
  
  // Close modal when clicking outside
  document.getElementById('aiResponseModal').addEventListener('click', function(e) {
    if (e.target.id === 'aiResponseModal') {
      closeAIResponseModal();
    }
  });
}

// Close AI response modal
function closeAIResponseModal() {
  const modal = document.getElementById('aiResponseModal');
  if (modal) {
    modal.remove();
  }
}

// Copy AI response to clipboard
function copyAIResponse() {
  const content = document.getElementById('aiResponseContent').innerText;
  navigator.clipboard.writeText(content).then(() => {
    // Show a brief confirmation
    const copyButton = document.getElementById('copyAIResponse');
    const originalText = copyButton.textContent;
    copyButton.textContent = 'Copied!';
    setTimeout(() => {
      copyButton.textContent = originalText;
    }, 2000);
  });
}

// Save AI response to database
async function saveAIResponse() {
  try {
    const pdfId = window.pdf_id || window.shared_pdf_id;
    if (!pdfId) {
      throw new Error('PDF ID not found');
    }
    
    if (!currentQuestion || !currentAnswer) {
      throw new Error('Question or answer is missing');
    }
    
    // Get CSRF token - try multiple methods
    let csrfToken = null;
    
    // Method 1: Look for CSRF token in meta tag
    const csrfMetaTag = document.querySelector('meta[name="csrf-token"]');
    if (csrfMetaTag) {
      csrfToken = csrfMetaTag.getAttribute('content');
    }
    
    // Method 2: Look for CSRF token in hidden input
    if (!csrfToken) {
      const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
      if (csrfInput) {
        csrfToken = csrfInput.value;
      }
    }
    
    // Method 3: Look for CSRF token in cookies
    if (!csrfToken) {
      const cookies = document.cookie.split(';');
      for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
          csrfToken = value;
          break;
        }
      }
    }
    
    if (!csrfToken) {
      throw new Error('CSRF token not found');
    }
    
    // Create form data
    const formData = new FormData();
    // Combine selected text with question for better context
    const fullQuestion = currentSelectedText ? 
      `Selected text: "${currentSelectedText}"\nQuestion: ${currentQuestion}` : 
      currentQuestion;
    formData.append('question', fullQuestion);
    formData.append('answer', currentAnswer);
    
    // Show saving indicator
    const saveButton = document.getElementById('saveAIResponse');
    const originalText = saveButton.textContent;
    saveButton.textContent = 'Saving...';
    saveButton.disabled = true;
    
    // Make request to backend to save the Q&A
    const url = `/pdf/ai/save_qa/${pdfId}`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': csrfToken
      }
    });
    
    // Restore button text
    saveButton.textContent = originalText;
    saveButton.disabled = false;
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    
    const data = await response.json();
    
    if (data.error) {
      throw new Error(data.error);
    }
    
    // Show success message
    alert('AI Q&A saved successfully!');
    
  } catch (error) {
    console.error('Error saving AI response:', error);
    alert('Error saving AI Q&A: ' + error.message);
    
    // Restore button
    const saveButton = document.getElementById('saveAIResponse');
    if (saveButton) {
      saveButton.textContent = 'Save';
      saveButton.disabled = false;
    }
  }
}

// Initialize AI features when the page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function() {
    // Add a small delay to ensure everything is loaded
    setTimeout(initializeAIFeatures, 100);
  });
} else {
  // Add a small delay to ensure everything is loaded
  setTimeout(initializeAIFeatures, 100);
}

// Function to summarize all annotations for the current PDF
async function summarizeAnnotations() {
  try {
    const pdfId = window.pdf_id || window.shared_pdf_id;
    if (!pdfId) {
      throw new Error('PDF ID not found');
    }
    
    // Get CSRF token - try multiple methods
    let csrfToken = null;
    
    // Method 1: Look for CSRF token in meta tag
    const csrfMetaTag = document.querySelector('meta[name="csrf-token"]');
    if (csrfMetaTag) {
      csrfToken = csrfMetaTag.getAttribute('content');
    }
    
    // Method 2: Look for CSRF token in hidden input
    if (!csrfToken) {
      const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
      if (csrfInput) {
        csrfToken = csrfInput.value;
      }
    }
    
    // Method 3: Look for CSRF token in cookies
    if (!csrfToken) {
      const cookies = document.cookie.split(';');
      for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
          csrfToken = value;
          break;
        }
      }
    }
    
    if (!csrfToken) {
      throw new Error('CSRF token not found');
    }
    
    // Show loading indicator
    showAIResponseModal('Generating summary...', true);
    
    const response = await fetch(`/pdf/ai/summarize/${pdfId}`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({length: 'medium'})
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (data.error) {
      throw new Error(data.error);
    }
    
    showAIResponseModal(data.summary || data.answer, false);
    
  } catch (error) {
    console.error('Error summarizing annotations:', error);
    showAIResponseModal('Error: ' + error.message, false);
  }
}
