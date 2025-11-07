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
