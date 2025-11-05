document.addEventListener('DOMContentLoaded', function () {
  const fileInput = document.querySelector('input[type="file"]');
  const fileLabelText = document.getElementById('file-label-text');
  const fileLabel = document.getElementById('file-label');

  if (fileInput && fileLabelText && fileLabel) {
    fileInput.addEventListener('change', function (e) {
      const hasFile = e.target.files.length > 0;
      const fileName = hasFile ? e.target.files[0].name : 'Choose PDF file';
      fileLabelText.textContent = fileName;

      fileLabel.classList.remove('btn-outline-primary', 'file-selected');

      if (hasFile) {
        fileLabel.classList.add('file-selected');
      } else {
        fileLabel.classList.add('btn-outline-primary');
      }
    });
  }
});

document.addEventListener('DOMContentLoaded', function() {
    const options = document.querySelectorAll('.document-type-option');
    
    options.forEach(option => {
      const radio = option.querySelector('input[type="radio"]');
      
      option.addEventListener('click', function() {
        // Rimuovi highlight da tutti
        options.forEach(opt => {
          opt.style.borderColor = '#dee2e6';
          opt.style.background = 'white';
        });
        
        // Seleziona questo
        radio.checked = true;
        option.style.borderColor = '#0d6efd';
        option.style.background = '#f0f7ff';
      });
      
      // Highlight iniziale per opzione selezionata
      if (radio.checked) {
        option.style.borderColor = '#0d6efd';
        option.style.background = '#f0f7ff';
      }
    });
  });