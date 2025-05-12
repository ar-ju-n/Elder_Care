document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.cooldown-timer').forEach(function(span) {
    let seconds = parseInt(span.getAttribute('data-seconds'));
    function update() {
      if (seconds > 0) {
        let mins = Math.floor(seconds / 60);
        let secs = seconds % 60;
        span.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
        seconds--;
        setTimeout(update, 1000);
      } else {
        // Optionally reload the page or enable the button
        span.closest('button').disabled = false;
        span.closest('button').classList.remove('btn-secondary');
        span.closest('button').classList.add('btn-primary');
        span.closest('button').innerHTML = '<i class="bi bi-chat-dots me-1"></i> Send Chat Request';
        // Optionally, you can redirect or reload
        // location.reload();
      }
    }
    update();
  });
});
