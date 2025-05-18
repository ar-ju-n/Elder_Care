// registration.js - Enhanced UX for registration forms with live validation, tooltips, accessibility, mobile tweaks

document.addEventListener('DOMContentLoaded', function() {
    // Password visibility toggle
    document.querySelectorAll('.toggle-password').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const targetId = btn.getAttribute('data-target');
            const input = document.getElementById(targetId);
            if (input) {
                if (input.type === 'password') {
                    input.type = 'text';
                    btn.innerHTML = '<i class="bi bi-eye-slash-fill" aria-label="Hide password"></i>';
                } else {
                    input.type = 'password';
                    btn.innerHTML = '<i class="bi bi-eye-fill" aria-label="Show password"></i>';
                }
            }
        });
    });

    // Real-time password match feedback
    const pwd1 = document.getElementById('id_password1');
    const pwd2 = document.getElementById('id_password2');
    if (pwd1 && pwd2) {
        let feedback = document.getElementById('pwd-match-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.id = 'pwd-match-feedback';
            feedback.className = 'form-text';
            pwd2.parentNode.appendChild(feedback);
        }
        function checkMatch() {
            if (pwd2.value.length > 0) {
                if (pwd1.value === pwd2.value) {
                    feedback.textContent = 'Passwords match!';
                    feedback.style.color = 'green';
                } else {
                    feedback.textContent = 'Passwords do not match.';
                    feedback.style.color = 'red';
                }
            } else {
                feedback.textContent = '';
            }
        }
        pwd1.addEventListener('input', checkMatch);
        pwd2.addEventListener('input', checkMatch);
    }

    // Live username/email validation (AJAX)
    function debounce(fn, ms) {
        let timer;
        return function(...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), ms);
        };
    }
    function showValidation(input, isValid, message) {
        let feedback = input.nextElementSibling;
        if (!feedback || !feedback.classList.contains('live-feedback')) {
            feedback = document.createElement('div');
            feedback.className = 'live-feedback form-text';
            input.parentNode.insertBefore(feedback, input.nextSibling);
        }
        feedback.textContent = message;
        feedback.classList.remove('valid-feedback', 'invalid-feedback');
        if (isValid) {
            feedback.classList.add('valid-feedback');
        } else {
            feedback.classList.add('invalid-feedback');
        }
    }
    // Username
    const usernameInput = document.getElementById('id_username');
    if (usernameInput) {
        usernameInput.setAttribute('aria-describedby', 'username-hint');
        usernameInput.setAttribute('autocomplete', 'username');
        usernameInput.setAttribute('title', 'Username must be unique. Letters, digits, @/./+/-/_ only.');
        usernameInput.insertAdjacentHTML('afterend', '<span id="username-hint" class="form-text">Letters, digits and @/./+/-/_ only. Must be unique.</span>');
        usernameInput.addEventListener('input', debounce(function() {
            const value = usernameInput.value.trim();
            if (value.length < 3) {
                showValidation(usernameInput, false, 'Username too short.');
                return;
            }
            fetch(`/accounts/api/check_username/?username=${encodeURIComponent(value)}`)
                .then(r => r.json())
                .then(data => {
                    if (data.available) {
                        showValidation(usernameInput, true, 'Username is available.');
                    } else {
                        showValidation(usernameInput, false, 'Username is taken.');
                    }
                })
                .catch(() => showValidation(usernameInput, false, 'Error checking username.'));
        }, 400));
    }
    // Email
    const emailInput = document.getElementById('id_email');
    if (emailInput) {
        emailInput.setAttribute('aria-describedby', 'email-hint');
        emailInput.setAttribute('autocomplete', 'email');
        emailInput.setAttribute('title', 'Enter a valid and unique email address.');
        emailInput.insertAdjacentHTML('afterend', '<span id="email-hint" class="form-text">A valid and unique email is required.</span>');
        emailInput.addEventListener('input', debounce(function() {
            const value = emailInput.value.trim();
            if (!value.match(/^[^@\s]+@[^@\s]+\.[^@\s]+$/)) {
                showValidation(emailInput, false, 'Invalid email format.');
                return;
            }
            fetch(`/accounts/api/check_email/?email=${encodeURIComponent(value)}`)
                .then(r => r.json())
                .then(data => {
                    if (data.available) {
                        showValidation(emailInput, true, 'Email is available.');
                    } else {
                        showValidation(emailInput, false, 'Email is already registered.');
                    }
                })
                .catch(() => showValidation(emailInput, false, 'Error checking email.'));
        }, 400));
    }
    // Password hints
    if (pwd1) {
        pwd1.setAttribute('aria-describedby', 'password-hint');
        pwd1.setAttribute('title', 'Password must be at least 8 characters and not too common.');
        pwd1.insertAdjacentHTML('afterend', '<span id="password-hint" class="form-text">At least 8 characters, not too common.</span>');
    }

    // Show/hide 'rate_per_hour' based on role
    const roleField = document.querySelector('select[name="role"]');
    const rateFieldDiv = document.getElementById('field-rate_per_hour');
    function toggleRateField() {
        if (roleField && rateFieldDiv) {
            if (roleField.value === "caregiver") {
                rateFieldDiv.style.display = "";
            } else {
                rateFieldDiv.style.display = "none";
            }
        }
    }
    if (roleField) {
        roleField.addEventListener('change', toggleRateField);
        toggleRateField(); // Initial check
    }

    // Accessibility: ensure all form controls have labels and ARIA attributes
    document.querySelectorAll('input,select,textarea').forEach(function(input) {
        if (!input.getAttribute('aria-label') && input.labels && input.labels.length > 0) {
            input.setAttribute('aria-label', input.labels[0].textContent);
        }
    });


    // Success message improvements
    const successDiv = document.querySelector('.registration-success');
    if (successDiv) {
        successDiv.setAttribute('role', 'alert');
        setTimeout(() => {
            successDiv.classList.add('animate__fadeOut');
        }, 4000);
    }

    // Auto-focus first input
    const firstInput = document.querySelector('.registration-card input[type="text"], .registration-card input[type="email"]');
    if (firstInput) {
        firstInput.focus();
    }
});
