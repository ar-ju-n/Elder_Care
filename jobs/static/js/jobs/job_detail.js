document.addEventListener('DOMContentLoaded', function() {
    // Share job functionality
    const shareBtn = document.getElementById('share-job-btn');
    if (shareBtn) {
        shareBtn.addEventListener('click', function() {
            if (navigator.share) {
                navigator.share({
                    title: document.title,
                    text: 'Check out this caregiving job',
                    url: window.location.href,
                })
                .then(() => console.log('Shared successfully'))
                .catch((error) => console.error('Error sharing:', error));
            } else {
                // Fallback for browsers that don't support Web Share API
                const url = window.location.href;
                navigator.clipboard.writeText(url).then(() => {
                    const tooltip = new bootstrap.Tooltip(shareBtn, {
                        title: 'Link copied to clipboard!',
                        trigger: 'manual'
                    });
                    tooltip.show();
                    setTimeout(() => tooltip.hide(), 2000);
                });
            }
        });
    }

    // Load job details via AJAX for SPA-like experience
    function loadJobDetails(jobId) {
        fetch(`/jobs/${jobId}/?ajax=1`)
            .then(response => response.json())
            .then(data => {
                updateJobDetails(data);
                updatePageTitle(data.title);
                updateUrl(jobId, data.title);
            })
            .catch(error => {
                console.error('Error loading job details:', error);
                showToast('Error loading job details. Please refresh the page.', 'danger');
            });
    }

    // Update the DOM with job details
    function updateJobDetails(job) {
        // Update job title and meta
        document.querySelector('.job-header h1').textContent = job.title;
        
        // Update job meta (location, pay, schedule)
        const metaContainer = document.querySelector('.job-meta');
        if (metaContainer) {
            metaContainer.innerHTML = `
                <span class="badge bg-primary">
                    <i class="fas fa-map-marker-alt me-1"></i> ${job.location}
                </span>
                <span class="badge bg-success">
                    <i class="fas fa-money-bill-wave me-1"></i> $${job.pay}/hr
                </span>
                <span class="badge bg-info text-dark">
                    <i class="fas fa-clock me-1"></i> ${job.schedule}
                </span>`;
        }
        
        // Update job description
        const descriptionEl = document.querySelector('.job-description');
        if (descriptionEl) {
            descriptionEl.innerHTML = job.description.replace(/\n/g, '<br>');
        }
        
        // Update action buttons
        updateActionButtons(job);
        
        // Update assigned caregiver section if exists
        updateAssignedCaregiver(job);
    }
    
    // Update action buttons based on job and user status
    function updateActionButtons(job) {
        const actionsContainer = document.querySelector('.job-actions');
        if (!actionsContainer) return;
        
        let buttonsHtml = '';
        
        // Back to jobs button
        buttonsHtml += `
            <a href="/jobs/" class="btn btn-outline-secondary">
                <i class="fas fa-arrow-left me-1"></i> Back to Jobs
            </a>`;
        
        // Apply/Application status button
        if (job.user_application) {
            let statusText = 'Application Submitted';
            let statusClass = 'btn-secondary';
            
            if (job.user_application.status === 'accepted') {
                statusText = 'Application Accepted';
                statusClass = 'btn-success';
            } else if (job.user_application.status === 'rejected') {
                statusText = 'Application Rejected';
                statusClass = 'btn-danger';
            }
            
            buttonsHtml += `
                <button class="btn ${statusClass} ms-2" disabled>
                    <i class="fas ${job.user_application.status === 'accepted' ? 'fa-check-circle' : 'fa-clock'} me-1"></i>
                    ${statusText}
                </button>`;
        } else if (job.can_apply) {
            buttonsHtml += `
                <a href="/jobs/${job.id}/apply/" class="btn btn-primary ms-2">
                    <i class="fas fa-paper-plane me-1"></i> Apply Now
                </a>`;
        }
        
        // Assign caregiver button (for job poster/admin)
        if (job.can_manage && !job.assigned_caregiver) {
            buttonsHtml += `
                <a href="/jobs/${job.id}/assign/" class="btn btn-outline-primary ms-2">
                    <i class="fas fa-user-plus me-1"></i> Assign Caregiver
                </a>`;
        }
        
        actionsContainer.innerHTML = buttonsHtml;
    }
    
    // Update assigned caregiver section
    function updateAssignedCaregiver(job) {
        const assignedSection = document.querySelector('.assigned-caregiver');
        if (!assignedSection) return;
        
        if (job.assigned_caregiver) {
            assignedSection.innerHTML = `
                <h5 class="section-title">Assigned Caregiver</h5>
                <div class="d-flex align-items-center">
                    <img src="${job.assigned_caregiver.avatar || '/static/img/default-avatar.png'}" 
                         alt="${job.assigned_caregiver.name}" class="user-avatar">
                    <div class="user-info">
                        <h6 class="mb-1">${job.assigned_caregiver.name}</h6>
                        <p class="mb-0">
                            <span class="badge bg-success">
                                <i class="fas fa-check-circle me-1"></i> Position Filled
                            </span>
                        </p>
                    </div>
                </div>`;
        } else {
            assignedSection.innerHTML = '';
        }
    }
    
    // Update page title
    function updatePageTitle(title) {
        document.title = `${title} | Elder Care Jobs`;
    }
    
    // Update URL without page reload
    function updateUrl(jobId, title) {
        const newUrl = `/jobs/${jobId}/`;
        window.history.pushState({ path: newUrl }, title, newUrl);
    }
    
    // Show toast notification
    function showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;
        
        const toastId = `toast-${Date.now()}`;
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        toast.id = toastId;
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>`;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Handle back/forward navigation
    window.addEventListener('popstate', function(event) {
        if (event.state && event.state.path) {
            const jobId = event.state.path.split('/').filter(Boolean).pop();
            if (jobId && !isNaN(jobId)) {
                loadJobDetails(jobId);
            }
        }
    });
});
