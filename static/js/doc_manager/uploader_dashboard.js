  if (ocrProcessingCount > 0 || pendingDocumentsCount > 0) {
    setTimeout(function() {
      location.reload();
    }, 30000); // 30 secondi
  }