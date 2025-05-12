// Enhanced focus styling for accessibility (admin)
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('button, a, input, select, textarea').forEach(function(el) {
    el.addEventListener('focus', function() {
      el.style.boxShadow = '0 0 0 3px #a3c4fa';
      el.style.outline = 'none';
    });
    el.addEventListener('blur', function() {
      el.style.boxShadow = '';
      el.style.outline = '';
    });
  });
});
