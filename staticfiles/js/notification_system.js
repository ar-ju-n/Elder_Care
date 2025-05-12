// notification_system.js - Browser notification system

// Request notification permission on page load
document.addEventListener('DOMContentLoaded', function() {
    requestNotificationPermission();
});

// Request permission to show notifications
function requestNotificationPermission() {
    if (!('Notification' in window)) {
        console.log('This browser does not support notifications');
        return;
    }

    if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
        Notification.requestPermission().then(function(permission) {
            if (permission === 'granted') {
                console.log('Notification permission granted');
            }
        });
    }
}

// Show a browser notification
function showNotification(title, options = {}) {
    // Default options
    const defaultOptions = {
        icon: '/static/img/logo.png',
        badge: '/static/img/badge.png',
        vibrate: [200, 100, 200],
        requireInteraction: false,
        silent: false
    };

    // Merge default options with provided options
    const notificationOptions = {...defaultOptions, ...options};

    // Check if notifications are supported and permission is granted
    if (!('Notification' in window)) {
        console.log('This browser does not support notifications');
        return;
    }

    if (Notification.permission === 'granted') {
        // Create and show notification
        const notification = new Notification(title, notificationOptions);
        
        // Add click handler to focus the window and navigate if URL is provided
        notification.onclick = function() {
            window.focus();
            if (options.url) {
                window.location.href = options.url;
            }
            notification.close();
        };

        // Auto close after 5 seconds if not requiring interaction
        if (!notificationOptions.requireInteraction) {
            setTimeout(() => {
                notification.close();
            }, 5000);
        }

        // Play sound if not silent
        if (!notificationOptions.silent && options.sound) {
            playNotificationSound(options.sound);
        }
    } else if (Notification.permission !== 'denied') {
        // Request permission again if not explicitly denied
        Notification.requestPermission().then(function(permission) {
            if (permission === 'granted') {
                showNotification(title, options);
            }
        });
    }
}

// Play notification sound
function playNotificationSound(soundName = 'default') {
    const sounds = {
        'default': '/static/sounds/notification.mp3',
        'message': '/static/sounds/message.mp3',
        'request': '/static/sounds/request.mp3'
    };

    const sound = new Audio(sounds[soundName] || sounds.default);
    sound.play().catch(e => console.log('Could not play notification sound:', e));
}

// Check if the window is currently visible/focused
function isWindowVisible() {
    return !document.hidden;
}

// Export functions for use in other scripts
window.notificationSystem = {
    requestPermission: requestNotificationPermission,
    showNotification: showNotification,
    isWindowVisible: isWindowVisible
};