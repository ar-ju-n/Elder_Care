// JS extracted from accounts/login.html
// (Paste the code from <script> blocks here)

document.addEventListener('DOMContentLoaded', function() {
  setTimeout(function() {
    document.querySelectorAll('.alert').forEach(function(alert) {
      alert.classList.add('animate__fadeOut');
      setTimeout(function() { alert.style.display = 'none'; }, 500);
    });
  }, 2000);
});
