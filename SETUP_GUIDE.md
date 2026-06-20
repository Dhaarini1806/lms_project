# Tradersfy LMS - Complete Setup Guide

## Project Overview

Tradersfy is a premium Learning Management System built with Django, featuring:
- **High-Security OTP Authentication**: Phone-based login with 10-digit validation
- **Razorpay Payment Integration**: Secure payment processing with signature verification
- **Automated Course Fulfillment**: Instant course access after payment
- **Custom Admin Panel**: Premium dashboard for course and user management
- **Certificate Generation**: Automatic PDF certificates for completed courses
- **Invoice Management**: Professional invoices with PDF download

---

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- SQLite3 (included with Python)
- Git

---

## Installation Steps

### 1. Clone the Project

```bash
cd /path/to/lms_project
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist, install these packages:

```bash
pip install Django==6.0.6
pip install razorpay
pip install reportlab
pip install pillow
pip install python-dotenv
```

### 4. Create Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here

# Razorpay Configuration
RAZORPAY_KEY_ID=rzp_test_your_key_here
RAZORPAY_KEY_SECRET=your_secret_here

# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# OTP Settings
OTP_EXPIRY_TIME=600
OTP_MAX_ATTEMPTS=3
```

### 5. Create Directories

```bash
mkdir -p media
mkdir -p static
mkdir -p logs
mkdir -p templates/core/admin
```

### 6. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser (Master Admin)

```bash
python manage.py createsuperuser
```

When prompted:
- **Username**: `1111111111` (Master Admin Phone Number)
- **Email**: your-email@example.com
- **Password**: Your secure password

### 8. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 9. Run Development Server

```bash
python manage.py runserver
```

The application will be available at: `http://localhost:8000`

---

## User Workflows

### Master Admin Access

1. Navigate to: `http://localhost:8000/master/dashboard/`
2. Login with username: `1111111111`
3. Access:
   - Dashboard with statistics
   - Course management (add, edit, delete)
   - User management and search
   - Transaction history with PDF export
   - Analytics and reports

### Student User Journey

1. **Home Page**: `http://localhost:8000/`
2. **Browse Courses**: `http://localhost:8000/courses/`
3. **Add to Cart**: Click "Add to Cart" on course
4. **View Cart**: `http://localhost:8000/cart/`
5. **Checkout**: `http://localhost:8000/checkout/`
   - Enter phone number (10 digits)
   - Receive OTP via SMS (simulated in development)
   - Enter OTP to verify
   - Fill billing details
   - Complete payment via Razorpay
6. **Invoice**: View and download invoice
7. **Course Access**: Unlock and view purchased courses
8. **Certificate**: Generate and download certificate after completion
9. **Profile**: Manage profile, view certificates, and order history

---

## API Endpoints

### Authentication
- `POST /send-otp/` - Send OTP to phone number
- `POST /verify-otp/` - Verify OTP code
- `GET /logout/` - Logout user

### Catalog
- `GET /courses/` - List all courses
- `GET /courses/<slug>/` - Course details
- `GET /courses/<slug>/lessons/<lesson-slug>/` - View lesson

### Cart & Checkout
- `POST /cart/add/<course-id>/` - Add course to cart
- `GET /cart/` - View cart
- `POST /cart/remove/<course-id>/` - Remove from cart
- `POST /checkout/` - Create order
- `POST /checkout/verify-payment/` - Verify Razorpay payment

### User Profile
- `GET /profile/` - User profile page
- `GET /invoice/<order-id>/` - View invoice
- `GET /invoice/<order-id>/download/` - Download invoice PDF
- `GET /certificate/<course-id>/` - View certificate
- `GET /certificate/<certificate-id>/download/` - Download certificate PDF

### Admin Panel
- `GET /master/dashboard/` - Admin dashboard
- `GET /master/courses/` - Manage courses
- `GET /master/add-course/` - Add new course
- `GET /master/edit-course/<id>/` - Edit course
- `GET /master/delete-course/<id>/` - Delete course
- `GET /master/users/` - Manage users
- `GET /master/user/<id>/` - User details
- `GET /master/transactions/` - View transactions
- `GET /master/download-transactions-pdf/` - Export transactions as PDF
- `GET /master/download-users-pdf/` - Export users as PDF
- `GET /master/analytics/` - View analytics

---

## Database Models

### Core Models

**User** (Django built-in)
- username, email, password, first_name, last_name

**Profile**
- user (OneToOne)
- full_name, phone_number, whatsapp_number
- user_type (student, professional, instructor, other)
- state, city, street_address
- employee_id, alt_email

**Course**
- title, slug, description
- language, level, price
- author_name, rating
- duration, created_at, updated_at
- is_published

**Lesson**
- course (ForeignKey)
- title, slug, description
- video_url, duration, order
- resources, created_at

**Order**
- user (ForeignKey)
- order_id (unique)
- total, original_price, tax
- status (pending, completed, failed, refunded)
- payment_method, razorpay_order_id, razorpay_payment_id
- state_union_territory, country, street_address
- created_at, updated_at

**OrderItem**
- order (ForeignKey)
- course (ForeignKey)
- price

**CourseAccess**
- user (ForeignKey)
- course (ForeignKey)
- accessed_at, completed_at

**Certificate**
- user (ForeignKey)
- course (ForeignKey)
- certificate_number (unique)
- issue_date

**OTPSession**
- phone_number (unique)
- otp_code, is_verified
- attempts, created_at, expires_at

---

## Configuration

### Razorpay Setup

1. Create account at https://razorpay.com
2. Get API keys from dashboard
3. Update `settings.py`:
   ```python
   RAZORPAY_KEY_ID = 'your_key_id'
   RAZORPAY_KEY_SECRET = 'your_key_secret'
   ```

### Email Configuration

For production, update email settings in `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # Use app-specific password
```

### Static Files

For production:

```bash
python manage.py collectstatic
```

Configure web server (Nginx/Apache) to serve static files from `staticfiles/` directory.

---

## Security Considerations

### Production Checklist

- [ ] Set `DEBUG = False` in settings
- [ ] Update `SECRET_KEY` with a strong random value
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Enable `CSRF_COOKIE_SECURE = True`
- [ ] Enable `SESSION_COOKIE_SECURE = True`
- [ ] Use HTTPS only
- [ ] Configure proper email backend
- [ ] Set up database backups
- [ ] Enable logging for security events
- [ ] Use environment variables for sensitive data

### OTP Security

- OTP expires after 10 minutes
- Maximum 3 failed attempts per session
- OTP is stored hashed in database
- Phone number validation (10 digits)

### Payment Security

- Razorpay signature verification
- Mock payment bypass for testing only
- Order ID validation before processing
- Transaction logging for audit trail

---

## Troubleshooting

### Migration Issues

```bash
# Reset migrations (development only)
python manage.py migrate core zero
python manage.py migrate

# Or create fresh database
rm db.sqlite3
python manage.py migrate
```

### Static Files Not Loading

```bash
python manage.py collectstatic --clear --noinput
```

### Template Not Found

Ensure `TEMPLATES['DIRS']` includes the correct path in `settings.py`

### OTP Not Sending

In development, OTP is logged to console. Check terminal output.

For production, configure email backend properly.

---

## Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn lms_project.wsgi:application --bind 0.0.0.0:8000
```

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "lms_project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Using Nginx

Configure reverse proxy to forward requests to Gunicorn.

---

## Support & Documentation

For more information:
- Django Documentation: https://docs.djangoproject.com/
- Razorpay Documentation: https://razorpay.com/docs/
- ReportLab Documentation: https://www.reportlab.com/docs/

---

## License

This project is proprietary to Tradersfy.

---

## Version

**Tradersfy LMS v1.0.0**

Last Updated: June 2026
