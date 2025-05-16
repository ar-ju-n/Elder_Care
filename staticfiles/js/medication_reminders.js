// Medication Reminders Browser Notification
// Requires: user is authenticated, reminders are rendered in a JS variable (see template injection below)

document.addEventListener('DOMContentLoaded', function() {
    if (!('Notification' in window)) return;
    if (Notification.permission !== 'granted') {
        Notification.requestPermission();
    }

    // This variable should be injected by the template
    if (typeof window.userMedicationReminders === 'undefined') return;

    function checkAndNotifyReminders() {
        const now = new Date();
        const nowHM = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
        window.userMedicationReminders.forEach(function(rem) {
            if (!rem.active) return;
            if (rem.notification_method !== 'browser') return;
            if (rem.time_of_day === nowHM && !rem._notified) {
                // Show notification
                const notif = new Notification('Medication Reminder', {
                    body: `${rem.medication_name}\n${rem.dosage ? 'Dosage: ' + rem.dosage + '\n' : ''}${rem.notes ? rem.notes : ''}`.trim(),
                    icon: '/static/img/pill.png'
                });
                rem._notified = true;
                setTimeout(() => { rem._notified = false; }, 60000); // allow again after 1 min
            }
        });
    }
    setInterval(checkAndNotifyReminders, 10000); // Check every 10s
});
