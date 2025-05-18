// Profile Page Enhancements

document.addEventListener('DOMContentLoaded', function() {
    // Live preview for profile picture
    const fileInput = document.querySelector('input[type="file"][name="profile_picture"]');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const previewImg = document.querySelector('#profile-edit-mode img.img-thumbnail');
            if (previewImg && fileInput.files && fileInput.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                };
                reader.readAsDataURL(fileInput.files[0]);
            }
        });
    }

    // Toast notification on profile update
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('updated') === '1') {
        showProfileToast('Profile updated successfully!');
    }
});

function showProfileToast(message) {
    let toast = document.getElementById('profile-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'profile-toast';
        toast.className = 'toast align-items-center text-bg-success border-0 position-fixed bottom-0 end-0 m-4';
        toast.style.zIndex = 1055;
        toast.innerHTML = `<div class="d-flex"><div class="toast-body">${message}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div>`;
        document.body.appendChild(toast);
    } else {
        toast.querySelector('.toast-body').textContent = message;
    }
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
}
