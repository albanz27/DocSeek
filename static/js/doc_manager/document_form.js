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
