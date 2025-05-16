// Medication Reminder Notification Bell Logic
// Assumes window.userMedicationReminders is available

document.addEventListener('DOMContentLoaded', function() {
    const bell = document.getElementById('notification-bell');
    const badge = document.getElementById('notification-badge');
    const dropdown = document.getElementById('notification-dropdown');
    if (!bell || !badge || !dropdown) return;
    
    function getDueReminders() {
        if (!window.userMedicationReminders) return [];
        const now = new Date();
        const nowHM = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
        return window.userMedicationReminders.filter(r => r.active && r.time_of_day === nowHM);
    }

    function updateBell() {
        const due = getDueReminders();
        if (due.length > 0) {
            badge.textContent = due.length;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
        // Populate dropdown
        dropdown.innerHTML = '';
        if (due.length === 0) {
            dropdown.innerHTML = '<div class="text-center text-muted">No medication reminders due now.</div>';
        } else {
            due.forEach(r => {
                const item = document.createElement('div');
                item.className = 'mb-2';
                item.innerHTML = `<strong>${r.medication_name}</strong><br>` +
                    (r.dosage ? `Dosage: ${r.dosage}<br>` : '') +
                    (r.notes ? `<em>${r.notes}</em><br>` : '') +
                    `<span class="text-secondary small">Time: ${r.time_of_day}</span>`;
                dropdown.appendChild(item);
            });
        }
    }

    // Initial update
    updateBell();
    // Update every 30 seconds
    setInterval(updateBell, 30000);

    // Optional: Show dropdown on bell click
    bell.addEventListener('click', function(e) {
        dropdown.classList.toggle('show');
        e.stopPropagation();
    });
    // Hide dropdown when clicking outside
    document.addEventListener('click', function() {
        dropdown.classList.remove('show');
    });
});
