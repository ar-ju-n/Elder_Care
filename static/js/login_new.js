// login_new.js: Modern login enhancements

document.addEventListener('DOMContentLoaded', function() {
  // Password visibility toggle
  const passwordInput = document.querySelector('input[type="password"]');
  if (passwordInput) {
    let toggleBtn = document.createElement('button');
    toggleBtn.type = 'button';
    toggleBtn.className = 'btn btn-outline-secondary btn-sm ms-2';
    toggleBtn.innerHTML = '<i class="bi bi-eye-slash" aria-hidden="true"></i>';
    toggleBtn.setAttribute('aria-label', 'Show password');
    passwordInput.parentNode.appendChild(toggleBtn);
    toggleBtn.addEventListener('click', function() {
      if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleBtn.innerHTML = '<i class="bi bi-eye" aria-hidden="true"></i>';
        toggleBtn.setAttribute('aria-label', 'Hide password');
      } else {
        passwordInput.type = 'password';
        toggleBtn.innerHTML = '<i class="bi bi-eye-slash" aria-hidden="true"></i>';
        toggleBtn.setAttribute('aria-label', 'Show password');
      }
    });
  }

  // Live username validation
  const usernameInput = document.querySelector('input[name="username"]');
  if (usernameInput) {
    let feedback = null;
    function showValidation(isValid, message) {
      if (!feedback) {
        feedback = document.createElement('div');
        feedback.className = 'form-text';
        usernameInput.parentNode.appendChild(feedback);
      }
      feedback.textContent = message;
      feedback.classList.remove('valid-feedback', 'invalid-feedback');
      if (isValid) {
        feedback.classList.add('valid-feedback');
      } else {
        feedback.classList.add('invalid-feedback');
      }
    }
    let debounceTimer;
    usernameInput.addEventListener('input', function() {
      clearTimeout(debounceTimer);
      const value = usernameInput.value.trim();
      if (value.length < 3) {
        showValidation(false, 'Username too short.');
        return;
      }
      debounceTimer = setTimeout(function() {
        fetch(`/accounts/api/check_username/?username=${encodeURIComponent(value)}`)
          .then(r => r.json())
          .then(data => {
            if (data.available) {
              showValidation(false, 'No such user found.');
            } else {
              showValidation(true, 'Username exists.');
            }
          })
          .catch(() => showValidation(false, 'Could not verify username.'));
      }, 400);
    });
  }

  // Password strength indicator
  if (passwordInput) {
    let strengthDiv = document.createElement('div');
    strengthDiv.className = 'form-text';
    passwordInput.parentNode.appendChild(strengthDiv);
    passwordInput.addEventListener('input', function() {
      const val = passwordInput.value;
      let score = 0;
      if (val.length >= 8) score++;
      if (/[A-Z]/.test(val)) score++;
      if (/[0-9]/.test(val)) score++;
      if (/[^A-Za-z0-9]/.test(val)) score++;
      if (val.length === 0) {
        strengthDiv.textContent = '';
        strengthDiv.classList.remove('valid-feedback', 'invalid-feedback');
      } else if (score <= 1) {
        strengthDiv.textContent = 'Weak password';
        strengthDiv.classList.remove('valid-feedback');
        strengthDiv.classList.add('invalid-feedback');
      } else if (score === 2 || score === 3) {
        strengthDiv.textContent = 'Moderate password';
        strengthDiv.classList.remove('valid-feedback', 'invalid-feedback');
      } else if (score === 4) {
        strengthDiv.textContent = 'Strong password';
        strengthDiv.classList.remove('invalid-feedback');
        strengthDiv.classList.add('valid-feedback');
      }
    });
  }
});
