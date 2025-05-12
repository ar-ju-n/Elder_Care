// Password visibility toggle

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-password').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const input = document.getElementById(this.dataset.target);
            if (input) {
                input.type = input.type === 'password' ? 'text' : 'password';
                this.classList.toggle('active');
            }
        });
    });
});
