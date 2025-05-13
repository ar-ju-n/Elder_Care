// Dark/Light Theme Toggle Script

document.addEventListener('DOMContentLoaded', function () {
    const themeToggle = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
    const darkIcon = document.querySelector('.theme-icon-dark');
    const lightIcon = document.querySelector('.theme-icon-light');

    function setTheme(theme) {
        // Set the theme attribute
        htmlElement.setAttribute('data-bs-theme', theme);

        // Store theme preference
        localStorage.setItem('theme', theme);

        // Update icons
        if (theme === 'dark') {
            if (darkIcon) darkIcon.classList.remove('d-none');
            if (lightIcon) lightIcon.classList.add('d-none');
            htmlElement.classList.add('dark-mode');
            htmlElement.classList.remove('light-mode');

            // Update navbar
            const navbar = document.querySelector('.navbar');
            if (navbar) {
                navbar.classList.add('navbar-dark');
                navbar.classList.remove('navbar-light');
            }

            // Update all tables
            document.querySelectorAll('table').forEach(table => {
                table.classList.add('table-dark');
            });

            // Update all cards
            document.querySelectorAll('.card').forEach(card => {
                card.classList.add('bg-dark');
                card.classList.add('text-light');
            });
        } else {
            if (darkIcon) darkIcon.classList.add('d-none');
            if (lightIcon) lightIcon.classList.remove('d-none');
            htmlElement.classList.remove('dark-mode');
            htmlElement.classList.add('light-mode');

            // Update navbar
            const navbar = document.querySelector('.navbar');
            if (navbar) {
                navbar.classList.remove('navbar-dark');
                navbar.classList.add('navbar-light');
            }

            // Update all tables
            document.querySelectorAll('table').forEach(table => {
                table.classList.remove('table-dark');
            });

            // Update all cards
            document.querySelectorAll('.card').forEach(card => {
                card.classList.remove('bg-dark');
                card.classList.remove('text-light');
            });
        }

        // Dispatch a custom event for other components to listen to
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    }

    // Check for saved theme preference or use user's system preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    // Apply initial theme
    if (savedTheme) {
        setTheme(savedTheme);
    } else if (prefersDark) {
        setTheme('dark');
    } else {
        setTheme('light');
    }

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            setTheme(e.matches ? 'dark' : 'light');
        }
    });

    // Toggle theme when button is clicked
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-bs-theme');
            setTheme(currentTheme === 'dark' ? 'light' : 'dark');
        });
    }
});
