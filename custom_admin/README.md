# Custom Admin Interface

This module provides a custom admin interface for the Elder Care project that mimics Django admin functionality while providing a more tailored and user-friendly experience.

## Features

- **Dashboard**: Overview of all apps and models with statistics
- **CRUD Operations**: Create, read, update, and delete functionality for all models
- **Filtering & Search**: Advanced filtering and search capabilities
- **Authentication**: Staff-only access with login protection
- **Bulk Operations**: Bulk delete and other actions
- **Responsive Design**: Mobile-friendly interface using Bootstrap

## Directory Structure

```
custom_admin/
├── __init__.py
├── admin.py
├── apps.py
├── forms.py          # Form utilities for the admin interface
├── migrations/
├── models.py
├── README.md         # This documentation file
├── static/
│   └── custom_admin/
│       ├── css/
│       │   └── admin.css
│       └── js/
│           └── admin.js
├── templatetags/
│   ├── __init__.py
│   └── admin_extras.py
├── tests.py
├── urls.py
├── utils.py          # Utility functions for the admin interface
└── views.py          # Admin views
```

## Templates

The templates for the custom admin interface are located in `templates/custom_admin/`:

```
templates/custom_admin/
├── admin_base.html           # Base template with navigation
├── admin_confirm_delete.html # Delete confirmation page
├── admin_dashboard.html      # Dashboard template
├── admin_form.html           # Form template for create/edit
├── admin_index.html          # Main index page with statistics
├── admin_list.html           # Basic list template
├── admin_list_filters.html   # Enhanced list with filters
├── admin_login.html          # Login page
└── admin_messages.html       # Flash messages template
```

## Usage

### URL Configuration

The custom admin is already configured in the main URLs file:

```python
path('custom_admin/', include('custom_admin.urls', namespace='custom_admin'))
```

### Accessing the Admin

Access the custom admin at `/custom_admin/`. Only staff users (is_staff=True) can access the admin interface.

### URL Patterns

- `/custom_admin/` - Dashboard
- `/custom_admin/login/` - Login page
- `/custom_admin/<app_label>/<model_name>/` - List view for a model
- `/custom_admin/<app_label>/<model_name>/add/` - Add new object
- `/custom_admin/<app_label>/<model_name>/<pk>/edit/` - Edit object
- `/custom_admin/<app_label>/<model_name>/<pk>/delete/` - Delete object
- `/custom_admin/<app_label>/<model_name>/bulk-delete/` - Bulk delete objects

## Extending the Admin

### Adding Custom Views

To add a custom view for a specific model:

1. Add a new view function in `views.py`
2. Add the URL pattern in `urls.py`
3. Create a template in `templates/custom_admin/`

### Customizing Forms

To customize forms for specific models, modify the `get_model_form` function in `forms.py`.

### Adding Custom Filters

To add custom filters for specific models, modify the `get_model_filters` function in `utils.py`.

## Security

The custom admin is secured with:

- `@login_required` decorator to ensure authentication
- `@user_passes_test(is_staff)` decorator to restrict access to staff users

## JavaScript Features

The admin interface includes JavaScript enhancements:

- Bulk selection with checkboxes
- Confirmation dialogs for delete actions
- Auto-hiding flash messages
- Filter form handling

## CSS Customization

The admin interface is styled with Bootstrap 5 and custom CSS in `static/custom_admin/css/admin.css`.
