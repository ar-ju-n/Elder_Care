// Prevent sidebar dropdown from collapsing when clicking links inside
// Only collapse when the toggle itself is clicked

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.sidebar-app-toggle').forEach(function(toggle) {
        // Only prevent default if href is '#', but let Bootstrap handle collapse
        toggle.addEventListener('click', function(e) {
            if (toggle.getAttribute('href') === '#') {
                e.preventDefault();
            }
        });

        var menuId = toggle.getAttribute('data-bs-target');
        var menu = document.querySelector(menuId);
        if (menu) {
            // Prevent collapse when clicking links inside the dropdown menu
            menu.querySelectorAll('a').forEach(function(link) {
                link.addEventListener('click', function (e) {
                    // Mark the menu as "clicked-inside" for the next collapse event
                    menu.setAttribute('data-prevent-collapse', 'true');
                });
            });

            // Listen for Bootstrap's hide.bs.collapse event
            menu.addEventListener('hide.bs.collapse', function (e) {
                if (menu.getAttribute('data-prevent-collapse') === 'true') {
                    e.preventDefault();
                    menu.removeAttribute('data-prevent-collapse');
                }
            });
        }
    });

    // Force logs dropdown to open upward (dropup)
    var logsDropdown = document.getElementById('downloadLogsDropdown');
    if (logsDropdown) {
        var parentLi = logsDropdown.closest('li.dropup');
        var dropdownMenu = parentLi ? parentLi.querySelector('.dropdown-menu') : null;
        if (parentLi && dropdownMenu) {
            logsDropdown.addEventListener('show.bs.dropdown', function () {
                parentLi.classList.add('dropup');
            });
            logsDropdown.addEventListener('hide.bs.dropdown', function () {
                parentLi.classList.remove('dropup');
            });
        }
    }
});


