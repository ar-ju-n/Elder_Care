// Real-time clock functionality

document.addEventListener('DOMContentLoaded', function() {
    function updateClock() {
        const clockElement = document.getElementById('current-time');
        if (!clockElement) return;
        const now = new Date();
        const userTimezone = clockElement.dataset.timezone;
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        if (userTimezone) {
            try {
                const tzOptions = {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false,
                    timeZone: userTimezone
                };
                clockElement.textContent = now.toLocaleTimeString(undefined, tzOptions);
            } catch(e) {
                clockElement.textContent = hours + ':' + minutes + ':' + seconds;
            }
        } else {
            clockElement.textContent = hours + ':' + minutes + ':' + seconds;
        }
    }
    updateClock();
    setInterval(updateClock, 1000);
});
