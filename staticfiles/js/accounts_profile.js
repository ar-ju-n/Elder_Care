// JS extracted from accounts/profile.html
// (Paste the code from <script> blocks here)

// AJAX for upvote and best answer actions on replies in topic_detail.html

document.addEventListener('DOMContentLoaded', function() {
    // --- Real-time notifications via WebSocket ---
    function setupNotificationWebSocket() {
        const bell = document.getElementById('notification-bell');
        if (!bell) return;
        let ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
        let ws_path = ws_scheme + '://' + window.location.host + '/ws/notifications/';
        let socket = new WebSocket(ws_path);
        socket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'notification' || data.unread_count !== undefined) {
                updateNotificationBadge(data.unread_count, true);
            }
        };
    }
    function playNotificationSound() {
        let audio = document.getElementById('notification-sound');
        if (!audio) {
            audio = document.createElement('audio');
            audio.id = 'notification-sound';
            audio.src = '/static/sounds/notification.mp3';
            audio.preload = 'auto';
            document.body.appendChild(audio);
        }
        audio.currentTime = 0;
        audio.play();
    }
    function flashBell() {
        const bell = document.getElementById('notification-bell');
        if (!bell) return;
        bell.classList.add('text-warning');
        setTimeout(() => bell.classList.remove('text-warning'), 1200);
    }
    function updateNotificationBadge(unread_count, isRealtime) {
        let badge = document.getElementById('notification-badge');
        if (badge) {
            if (unread_count > 0) {
                badge.textContent = unread_count;
                badge.style.display = '';
                if (isRealtime) {
                    playNotificationSound();
                    flashBell();
                }
            } else {
                badge.style.display = 'none';
            }
        }
    }
    setupNotificationWebSocket();

    // --- Notification dropdown AJAX ---
    const bellDropdown = document.getElementById('notification-bell-dropdown');
    const dropdown = document.getElementById('notification-dropdown');
    if (bellDropdown && dropdown) {
        let loaded = false;
        function loadNotifications() {
            fetch('/forum/notifications/api/recent/')
                .then(resp => resp.json())
                .then(data => {
                    dropdown.innerHTML = '';
                    if (data.notifications.length === 0) {
                        dropdown.innerHTML = '<div class="text-center text-muted">No notifications</div>';
                    } else {
                        data.notifications.forEach(n => {
                            dropdown.innerHTML += `<a href="${n.url}" class="dropdown-item${n.is_read ? '' : ' fw-bold'}">${n.message}<br><small class="text-muted">${n.created_at}</small></a>`;
                        });
                        dropdown.innerHTML += '<div class="dropdown-divider"></div><button id="mark-all-read" class="btn btn-sm btn-link w-100">Mark all as read</button>';
                        dropdown.innerHTML += '<a href="/forum/notifications/" class="btn btn-sm btn-outline-secondary w-100 mt-1">View all notifications</a>';
                        document.getElementById('mark-all-read').onclick = function() {
                            fetch('/forum/notifications/api/mark_read/', {method: 'POST', headers: {'X-CSRFToken': getCSRFToken()}})
                                .then(() => { loaded = false; loadNotifications(); updateNotificationBadge(0); });
                        };
                    }
                });
        }
        function getCSRFToken() {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, 10) === ('csrftoken=')) {
                        cookieValue = decodeURIComponent(cookie.substring(10));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        bellDropdown.addEventListener('show.bs.dropdown', function() {
            if (!loaded) {
                loadNotifications();
                loaded = true;
            }
        });
    }

    // --- AJAX for upvote/best answer ---
    var repliesList = document.getElementById('replies-list');
    if (!repliesList) return;
    function attachAjaxToReplyForms() {
        document.querySelectorAll('#replies-list form[action=""]').forEach(function(form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                const formData = new FormData(form);
                fetch(window.location.href, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
                    },
                    body: formData
                })
                .then(response => response.text())
                .then(html => {
                    // Replace the replies list with the updated HTML
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const updatedReplies = doc.getElementById('replies-list');
                    if (updatedReplies) {
                        repliesList.replaceWith(updatedReplies);
                        repliesList = updatedReplies;
                        attachAjaxToReplyForms();
                    }
                });
            }, {once: true});
        });
    }
    attachAjaxToReplyForms();
});
