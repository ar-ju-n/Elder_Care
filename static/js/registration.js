document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Toggle password visibility
    const togglePasswordButtons = document.querySelectorAll('.toggle-password');
    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const passwordInput = targetId ? document.getElementById(targetId) : 
                this.closest('.input-group').querySelector('input');
            
            if (passwordInput) {
                const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordInput.setAttribute('type', type);
                this.querySelector('i').classList.toggle('bi-eye');
                this.querySelector('i').classList.toggle('bi-eye-slash');
            }
        });
    });

    // Profile picture preview and upload
    const profilePictureInput = document.getElementById('id_profile_picture');
    const profilePreview = document.getElementById('profile-preview');
    const profileUploadBtn = document.querySelector('.profile-upload-btn');
    const profilePictureContainer = document.querySelector('.profile-picture-container');
    
    if (profilePictureContainer && profilePictureInput) {
        // Make the entire profile picture area clickable
        profilePictureContainer.addEventListener('click', function(e) {
            // If clicking on the camera icon, let the button's click handler handle it
            if (e.target.closest('.profile-upload-btn')) {
                return;
            }
            // Otherwise, trigger file input
            profilePictureInput.click();
        });
        
        // Handle file selection
        profilePictureInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Check file type
                const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
                if (!validTypes.includes(file.type)) {
                    alert('Please select a valid image file (JPEG, PNG, or GIF)');
                    return;
                }
                
                // Check file size (max 2MB)
                const maxSize = 2 * 1024 * 1024; // 2MB
                if (file.size > maxSize) {
                    alert('Image size should be less than 2MB');
                    return;
                }
                
                // Show preview
                const reader = new FileReader();
                reader.onload = function(e) {
                    if (profilePreview) {
                        profilePreview.src = e.target.result;
                        profilePreview.classList.add('uploaded');
                    }
                };
                reader.readAsDataURL(file);
            }
        });
        
        // Handle camera icon click
        if (profileUploadBtn) {
            profileUploadBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                profilePictureInput.click();
            });
        }
    }

    // Password strength indicator
    const passwordInput = document.getElementById('id_password1');
    const passwordStrengthBar = document.getElementById('password-strength-bar');
    const passwordStrengthBarInner = passwordStrengthBar ? passwordStrengthBar.querySelector('.progress-bar') : null;
    
    if (passwordInput && passwordStrengthBar && passwordStrengthBarInner) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const strength = calculatePasswordStrength(password);
            updatePasswordStrengthBar(strength);
        });
    }

    function calculatePasswordStrength(password) {
        let strength = 0;
        
        // Length check
        if (password.length >= 8) strength += 20;
        if (password.length >= 12) strength += 10;
        
        // Contains lowercase
        if (/[a-z]/.test(password)) strength += 10;
        
        // Contains uppercase
        if (/[A-Z]/.test(password)) strength += 10;
        
        // Contains numbers
        if (/[0-9]/.test(password)) strength += 10;
        
        // Contains special characters
        if (/[^A-Za-z0-9]/.test(password)) strength += 20;
        
        // Contains common patterns (deduct points)
        if (/(.)\1{2,}/.test(password)) strength = Math.max(0, strength - 10);
        
        return Math.min(100, Math.max(0, strength));
    }

    function updatePasswordStrengthBar(strength) {
        if (!passwordStrengthBar || !passwordStrengthBarInner) return;
        
        passwordStrengthBar.style.display = 'block';
        passwordStrengthBarInner.style.width = strength + '%';
        
        // Update color based on strength
        if (strength < 30) {
            passwordStrengthBarInner.className = 'progress-bar bg-danger';
        } else if (strength < 70) {
            passwordStrengthBarInner.className = 'progress-bar bg-warning';
        } else {
            passwordStrengthBarInner.className = 'progress-bar bg-success';
        }
    }

    // Form validation
    const form = document.querySelector('.needs-validation');
    if (form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    }
});
