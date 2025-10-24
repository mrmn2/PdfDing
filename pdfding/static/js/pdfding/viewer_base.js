function start_viewer(page_number, pdf_url, tab_title) {
  // open pdf on the start page
  window.addEventListener('load', function() {
      PDFViewerApplication.initialBookmark = "page="+page_number;
      PDFViewerApplication.open({ url: pdf_url });
      // overwrite setTitle so that PdfDing controls the tab's title
      PDFViewerApplication.setTitle = function set_new_title(new_title) {
        const editorIndicator = this._hasAnnotationEditors;
        document.title = `${editorIndicator ? "* " : ""}${tab_title}`;
      }
  });

  // set properties
  document.addEventListener("webviewerloaded", () => {
    PDFViewerApplicationOptions.set('disablePreferences', true); // needed otherwise settings are not overwritten
    PDFViewerApplicationOptions.set('disableHistory', true); // disable browsing history, clicking on chapters does not open new page
    PDFViewerApplicationOptions.set('viewOnLoad', 1  ); // disable remembering page
    PDFViewerApplicationOptions.set("workerSrc", "../../static/pdfjs/build/pdf.worker.mjs");
  });
}
