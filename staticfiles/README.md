# Elder Care - Frontend Documentation

This directory contains all static assets (CSS, JavaScript, images, etc.) for the Elder Care application.

## Directory Structure

```
static/
├── css/
│   ├── components/     # Reusable component styles
│   ├── pages/          # Page-specific styles
│   ├── main.css        # Global styles and variables
│   └── vendor/         # Third-party CSS files
├── js/
│   ├── components/    # Reusable JavaScript components
│   ├── pages/         # Page-specific JavaScript
│   ├── utils.js       # Utility functions
│   ├── form-handler.js # Form handling logic
│   └── main.js        # Main JavaScript entry point
├── images/            # Image assets
└── fonts/             # Custom fonts
```

## JavaScript Architecture

The frontend JavaScript is organized into modules for better maintainability and code organization.

### Core Modules

1. **main.js**
   - Initializes all components when the DOM is loaded
   - Sets up global error handling
   - Provides core functionality

2. **utils.js**
   - Contains utility functions:
     - `debounce`: Limits how often a function can be called
     - `formatDate`: Formats dates consistently
     - `formatCurrency`: Formats numbers as currency
     - `togglePasswordVisibility`: Toggles password field visibility
     - `copyToClipboard`: Copies text to clipboard
     - `getUrlParams`: Gets URL parameters
     - `updateUrlParams`: Updates URL parameters without page reload

3. **form-handler.js**
   - Handles form submissions and validation
   - Provides AJAX form submission
   - Includes file upload handling
   - Manages form state and feedback

### Using the Toast Notification System

To show a toast notification:

```javascript
// Basic usage
showToast('Operation completed successfully', 'success');

// With custom duration
showToast('Saving changes...', 'info', 3000);

// Available types: success, error, warning, info
```

### Form Handling

To make a form submit via AJAX:

1. Add `data-ajax-form` attribute to your form
2. The form will be automatically handled by `form-handler.js`

```html
<form method="post" action="/submit/" data-ajax-form>
    {% csrf_token %}
    <!-- form fields -->
    <button type="submit" class="btn btn-primary">Submit</button>
</form>
```

### Adding New JavaScript Components

1. Create a new file in `static/js/components/`
2. Export your component as a module
3. Import and initialize it in `main.js`

## CSS Architecture

### Global Styles

- **main.css**: Contains global styles, variables, and utility classes
- **components/**: Reusable UI components (buttons, cards, modals, etc.)
- **pages/**: Page-specific styles

### CSS Variables

Define colors, spacing, and other design tokens as CSS variables in `main.css`:

```css
:root {
    --primary: #4e73df;
    --success: #1cc88a;
    --danger: #e74a3b;
    --warning: #f6c23e;
    --info: #36b9cc;
    --dark: #5a5c69;
    --light: #f8f9fc;
    
    --spacing-unit: 1rem;
    --border-radius: 0.35rem;
    --box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
}
```

## Best Practices

1. **JavaScript**
   - Use ES6+ syntax
   - Keep functions small and focused
   - Add JSDoc comments for functions
   - Handle errors gracefully
   - Use event delegation for dynamic content

2. **CSS**
   - Use BEM naming convention for complex components
   - Keep selectors shallow (max 3 levels deep)
   - Use CSS variables for theming
   - Mobile-first responsive design

3. **Performance**
   - Lazy load non-critical resources
   - Minify and bundle CSS/JS in production
   - Optimize images
   - Use appropriate image formats (WebP with fallbacks)

## Development Workflow

1. Make changes to the appropriate files
2. Test in multiple browsers
3. Ensure responsive behavior works as expected
4. Run any build processes if needed
5. Commit changes with descriptive messages

## Browser Support

- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Edge (latest 2 versions)
- Safari (latest 2 versions)
- Mobile Safari (latest 2 versions)
- Chrome for Android (latest 2 versions)
