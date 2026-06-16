# 🚀 Quick Start Guide - Get Running in 5 Minutes!

## Step 1: Install Python Packages (1 minute)

Open PowerShell in your project directory and run:

```bash
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed Django-4.2.7 mysqlclient-2.2.0 python-decouple-3.8 ...
```

---

## Step 2: Setup MySQL Database (2 minutes)

### Option A: Using MySQL Workbench (Easier)  // or insall xampp 
1. Open MySQL Workbench
2. Click on your connection
3. Run this query:
   ```sql
   CREATE DATABASE beamy_erp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

### Option B: Using Command Line
```bash
# Login to MySQL
mysql -u root -p

# Create database
CREATE DATABASE beamy_erp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Exit
exit;
```
## ALternative 
Install XAMPP (If You Don't Have MySQL Installed)

If MySQL is not installed, install **XAMPP**. It includes:

-   Apache\
-   MySQL (MariaDB)\
-   phpMyAdmin

### Steps:

1.  Download & install XAMPP\
2.  Open XAMPP Control Panel\
3.  Click **Start** next to **MySQL**\
4.  Click **Admin** (opens phpMyAdmin)\
5.  Click **New**\
6.  Enter database name: `beamy_erp`\
7.  Select collation: `utf8mb4_unicode_ci`\
8.  Click **Create**

✅ Done! Your database is ready.





## Step 4: Run Migrations (1 minute)

```bash
# Create migration files
python manage.py makemigrations

# Apply migrations to database
python manage.py migrate
```

**Expected output:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions, core, inventory, production, hr, finance, suppliers
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
```

---

## Step 5: Create Test Users (30 seconds)

```bash
python manage.py create_initial_users
```

**Expected output:**
```
Creating initial users...
✓ Admin user created: admin@beamysports.com
✓ Inventory Manager created: inventory@beamysports.com
✓ Production Manager created: production@beamysports.com
✓ HR Manager created: hr@beamysports.com
✓ Finance Manager created: finance@beamysports.com
✓ Supplier Manager created: supplier@beamysports.com
All users created successfully!
```

---

## Step 6: Start Server (10 seconds)

```bash
python manage.py runserver
```

**Expected output:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

## Step 7: Access Application (NOW!)

Open your browser and go to:

### 🌐 Main Application
**URL**: http://localhost:8000/

### 🔐 Login Credentials

| Role | Email | Password |
|------|-------|----------|
| **Admin** | admin@beamysports.com | admin123 |
| **Inventory Manager** | inventory@beamysports.com | inventory123 |
| **Production Manager** | production@beamysports.com | production123 |
| **HR Manager** | hr@beamysports.com | hr123 |
| **Finance Manager** | finance@beamysports.com | finance123 |
| **Supplier Manager** | supplier@beamysports.com | supplier123 |

---

OR you can login with usernames too

## Login Credentials

- Admin: admin / admin123
- Inventory Manager: inventory / inventory123
- Production Manager: production / production123
- HR Manager: hr / hr123
- Finance Manager: finance / finance123
- Purchase Manager: supplier / supplier123

## 🎉 You're Done!

Your ERP system is now running. Try logging in with any of the accounts above.

---

## ❌ If You Get Errors

### Error: "No module named 'decouple'"
```bash
pip install python-decouple
```

### Error: "No module named 'MySQLdb'"
```bash
pip install mysqlclient
```

