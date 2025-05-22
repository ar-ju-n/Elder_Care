// moderation.js: AJAX for admin moderation of chat messages and forum replies

document.addEventListener('DOMContentLoaded', function() {
    // Utility: CSRF fetch
    function csrfFetch(url, options={}) {
        options.headers = options.headers || {};
        options.headers['X-CSRFToken'] = getCookie('csrftoken');
        options.headers['X-Requested-With'] = 'XMLHttpRequest';
        return fetch(url, options);
    }
    // Utility: get CSRF from cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Tab switching
    const tabBtns = document.querySelectorAll('.moderation-tab-btn');
    tabBtns.forEach(btn => btn.addEventListener('click', function() {
        tabBtns.forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        document.querySelectorAll('.moderation-tab').forEach(tab => tab.classList.add('d-none'));
        document.getElementById(this.dataset.target).classList.remove('d-none');
    }));

    // Load messages and replies
    function loadModeration(type, status) {
        let url = '';
        if (type === 'messages') url = '/custom_admin/api/moderation/messages/?status=' + status;
        else url = '/custom_admin/api/moderation/replies/?status=' + status;
        fetch(url).then(r => r.json()).then(data => {
            const tbody = document.querySelector(`#${type}Table tbody`);
            tbody.innerHTML = '';
            (data[type] || []).forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = type === 'messages' ? `
                    <td>${item.id}</td>
                    <td>${item.sender_id}</td>
                    <td>${item.message}</td>
                    <td>${item.timestamp}</td>
                    <td>${item.is_approved ? 'Yes' : 'No'}</td>
                    <td>${item.is_flagged ? 'Yes' : 'No'}</td>
                    <td>${item.moderation_notes || ''}</td>
                    <td class="d-flex gap-2">
                        <button class="btn btn-success btn-sm" data-action="approve" data-id="${item.id}">Approve</button>
                        <button class="btn btn-danger btn-sm" data-action="reject" data-id="${item.id}">Reject</button>
                        <button class="btn btn-warning btn-sm" data-action="flag" data-id="${item.id}">Flag</button>
                        <button class="btn btn-secondary btn-sm" data-action="delete" data-id="${item.id}">Delete</button>
                    </td>
                ` : `
                    <td>${item.id}</td>
                    <td>${item.author_id}</td>
                    <td>${item.body}</td>
                    <td>${item.created_at}</td>
                    <td>${item.is_approved ? 'Yes' : 'No'}</td>
                    <td>${item.is_flagged ? 'Yes' : 'No'}</td>
                    <td>${item.moderation_notes || ''}</td>
                    <td class="d-flex gap-2">
                        <button class="btn btn-success btn-sm" data-action="approve" data-id="${item.id}">Approve</button>
                        <button class="btn btn-danger btn-sm" data-action="reject" data-id="${item.id}">Reject</button>
                        <button class="btn btn-warning btn-sm" data-action="flag" data-id="${item.id}">Flag</button>
                        <button class="btn btn-secondary btn-sm" data-action="delete" data-id="${item.id}">Delete</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        });
    }
    // Initial load
    loadModeration('messages', 'pending');
    loadModeration('replies', 'pending');

    // Filter buttons
    document.querySelectorAll('.moderation-status-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const type = this.dataset.type;
            const status = this.dataset.status;
            loadModeration(type, status);
        });
    });

    // Moderation actions
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-action][data-id]')) {
            const type = e.target.closest('table').id.replace('Table', '');
            const id = e.target.dataset.id;
            const action = e.target.dataset.action;
            let url = type === 'messages' ? '/custom_admin/api/moderation/messages/' : '/custom_admin/api/moderation/replies/';
            csrfFetch(url, {
                method: 'POST',
                body: JSON.stringify({ id, action })
            }).then(r => r.json()).then(data => {
                if (data.success) {
                    loadModeration(type, 'pending');
                } else {
                    alert(data.error || 'Moderation action failed');
                }
            });
        }
    });
});
