# Templates Directory

## Structure

Move your HTML files to the appropriate directories:

```
templates/
├── core/
│   ├── login.html              (from login.html)
│   ├── dashboard.html          (from dashboard.html)
│   ├── admin.html              (from admin.html)
│   ├── profile.html            (from profile.html)
│   ├── change_password.html    (from change password.html)
│   ├── help.html               (from help.html)
│   └── notifications.html      (new)
│
├── inventory/
│   └── dashboard.html          (from inventory.html)
│
├── production/
│   └── dashboard.html          (from Production.html)
│
├── hr/
│   └── dashboard.html          (from HR.html)
│
├── finance/
│   └── dashboard.html          (from FinanceModule.html)
│
└── suppliers/
    └── dashboard.html          (from SuppliersModule.html)
```

## Template Conversion Steps

For each HTML file:

1. **Add template tags at the top:**
```django
{% load static %}
<!DOCTYPE html>
```

2. **Update CSS links:**
```html
<link rel="stylesheet" href="{% static 'style.css' %}">
```

3. **Update JS links:**
```html
<script src="{% static 'main.js' %}"></script>
```

4. **Update image sources:**
```html
<img src="{% static 'sources/beamy.png' %}">
```

5. **Update navigation links:**
```html
<a href="{% url 'core:dashboard' %}">Dashboard</a>
<a href="{% url 'inventory:dashboard' %}">Inventory</a>
<a href="{% url 'production:dashboard' %}">Production</a>
<a href="{% url 'hr:dashboard' %}">HR</a>
<a href="{% url 'finance:dashboard' %}">Finance</a>
<a href="{% url 'suppliers:dashboard' %}">Suppliers</a>
<a href="{% url 'core:admin_dashboard' %}">Admin</a>
<a href="{% url 'core:help' %}">Help</a>
<a href="{% url 'core:logout' %}">Logout</a>
```

6. **Add CSRF token to all forms:**
```html
<form method="POST">
    {% csrf_token %}
    <!-- form fields -->
</form>
```

7. **Display user information:**
```html
<div class="user-info">
    <p>{{ user.first_name }} {{ user.last_name }}</p>
    <p>{{ user.get_role_display }}</p>
</div>
```

8. **Show Django messages:**
```html
{% if messages %}
    {% for message in messages %}
        <div class="alert alert-{{ message.tags }}">
            {{ message }}
        </div>
    {% endfor %}
{% endif %}
```

## Example: Converting login.html

### Before (Static HTML):
```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <form id="login-form">
        <input type="text" name="username">
        <input type="password" name="password">
        <button type="submit">Login</button>
    </form>
</body>
</html>
```

### After (Django Template):
```html
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="{% static 'style.css' %}">
</head>
<body>
    {% if messages %}
        {% for message in messages %}
            <div class="alert alert-{{ message.tags }}">
                {{ message }}
            </div>
        {% endfor %}
    {% endif %}
    
    <form method="POST">
        {% csrf_token %}
        <input type="text" name="username" required>
        <input type="password" name="password" required>
        <button type="submit">Login</button>
    </form>
</body>
</html>
```

## Quick Conversion Script

You can use this find-and-replace pattern:

1. Find: `href="style.css"`
   Replace: `href="{% static 'style.css' %}"`

2. Find: `src="main.js"`
   Replace: `src="{% static 'main.js' %}"`

3. Find: `src="sources/`
   Replace: `src="{% static 'sources/`

4. Find: `href="dashboard.html"`
   Replace: `href="{% url 'core:dashboard' %}"`

5. Find: `href="inventory.html"`
   Replace: `href="{% url 'inventory:dashboard' %}"`

6. Find: `href="Production.html"`
   Replace: `href="{% url 'production:dashboard' %}"`

7. Find: `href="HR.html"`
   Replace: `href="{% url 'hr:dashboard' %}"`

8. Find: `href="FinanceModule.html"`
   Replace: `href="{% url 'finance:dashboard' %}"`

9. Find: `href="SuppliersModule.html"`
   Replace: `href="{% url 'suppliers:dashboard' %}"`

10. Find: `href="admin.html"`
    Replace: `href="{% url 'core:admin_dashboard' %}"`

11. Find: `href="login.html"`
    Replace: `href="{% url 'core:login' %}"`

12. Find: `<form`
    Replace: `<form method="POST">{% csrf_token %}`

## Testing Templates

After conversion, test each page:

```bash
python manage.py runserver
```

Visit each URL and check:
- [ ] Static files load correctly
- [ ] Links work properly
- [ ] Forms submit correctly
- [ ] User info displays
- [ ] Messages show up
- [ ] No 404 errors

## Common Issues

### Static files not loading
- Run: `python manage.py collectstatic`
- Check STATIC_URL in settings.py
- Verify files are in static/ folder

### Template not found
- Check file is in correct templates/ subfolder
- Verify template name in view matches file name
- Check TEMPLATES setting in settings.py

### CSRF token missing
- Add `{% csrf_token %}` inside all POST forms
- Check MIDDLEWARE includes CsrfViewMiddleware

### URL not found
- Check URL name in urls.py
- Verify app_name is set
- Use correct namespace: `app_name:url_name`
