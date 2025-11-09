let currentPage = {initial_page};
const iframe = document.getElementById('pdf-viewer');

function updatePageInfo() {
    document.getElementById('page-info').textContent = `Page ${currentPage}`;
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        iframe.contentWindow.PDFViewerApplication.page = currentPage;
        updatePageInfo();
    }
}

function nextPage() {
    currentPage++;
    iframe.contentWindow.PDFViewerApplication.page = currentPage;
    updatePageInfo();
}

function zoomIn() {
    iframe.contentWindow.PDFViewerApplication.zoomIn();
}

function zoomOut() {
    iframe.contentWindow.PDFViewerApplication.zoomOut();
}

function fitToPage() {
    iframe.contentWindow.PDFViewerApplication.pdfViewer.currentScaleValue = 'page-fit';
}

// Ascolta i cambiamenti di pagina dall'iframe
iframe.addEventListener('load', function() {
    try {
        const pdfApp = iframe.contentWindow.PDFViewerApplication;
        pdfApp.eventBus.on('pagechanging', function(evt) {
            currentPage = evt.pageNumber;
            updatePageInfo();
        });
    } catch (e) {
        console.log('PDF.js event binding:', e);
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowLeft') previousPage();
    if (e.key === 'ArrowRight') nextPage();
    if (e.key === '+' || e.key === '=') zoomIn();
    if (e.key === '-') zoomOut();
});