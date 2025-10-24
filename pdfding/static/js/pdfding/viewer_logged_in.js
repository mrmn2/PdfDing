// function for updating the remote page
function update_remote_page(pdf_id, update_url, csrf_token) {
  if (PDFViewerApplication.pdfViewer.currentPageNumber != page_number) {
    page_number = PDFViewerApplication.pdfViewer.currentPageNumber;
    set_current_page(page_number, pdf_id, update_url, csrf_token);
  }
}

// function for settings current page
function set_current_page(current_page, pdf_id, update_url, csrf_token) {
  var form_data = new FormData();
  form_data.append('pdf_id', pdf_id)
  form_data.append('current_page', current_page)

  fetch(update_url, {
    method: "POST",
    body: form_data,
    headers: {
      'X-CSRFToken': csrf_token,
    },
  });
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
