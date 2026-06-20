# Tradersfy LMS

## Overview

Tradersfy is a high-security, streamlined Learning Management System (LMS) designed for rapid user onboarding and automated product delivery. This project implements a comprehensive workflow from user authentication to course fulfillment, certificate generation, and a custom administrative panel.

## Key Features

- **Enhanced Authentication Pipeline**: Secure OTP-based login with phone number validation and session management.
- **Transactional Integrity and Verification**: Seamless integration with Razorpay for secure payments, including signature enforcement and mock transaction handling for testing.
- **Automated Post-Purchase Fulfillment**: Instant course access upon successful payment, with order status updates and session cleanup.
- **Custom Admin Panel**: A premium, amber-on-black themed administrative interface for managing courses, users, transactions, and viewing analytics. Includes PDF export functionality for user and transaction reports.
- **Comprehensive User Workflow**: Covers the entire user journey from browsing courses, adding to cart, checkout, login, fulfillment, invoice generation (with PDF download), course access, lesson viewing, course completion, certificate generation (with PDF download), and profile management.
- **Dynamic Frontend Templates**: All user-facing and admin-facing templates are designed with a consistent, modern glassmorphism/dark theme.

## Project Structure

The project is built using Django and follows a modular structure:

- `core/`: Contains the main application logic, including models, views, templates, and static files.
  - `models.py`: Defines the database schema for courses, lessons, users, orders, certificates, and OTP sessions.
  - `views.py`: Handles core application logic, including authentication, course catalog, cart, checkout, and user profile.
  - `admin_views.py`: Implements the custom admin panel logic and PDF generation for reports.
  - `invoice_views.py`: Manages invoice and certificate generation and PDF downloads.
  - `urls.py`: Defines all URL routes for the application.
  - `templates/`: HTML templates for both frontend and custom admin panel.
  - `static/`: Static assets like CSS, JavaScript, and images.
- `lms_project/`: Project-level settings and URL configurations.
  - `settings.py`: Configures Django, database, static/media files, Razorpay, email, and OTP settings.
  - `urls.py`: Main URL dispatcher.
- `requirements.txt`: Lists all Python dependencies.
- `SETUP_GUIDE.md`: Detailed instructions for setting up, configuring, and deploying the project.

## Getting Started

For detailed instructions on how to set up, configure, and run the Tradersfy LMS project, please refer to the [SETUP_GUIDE.md](SETUP_GUIDE.md) file.

## Technologies Used

- **Backend**: Django (Python)
- **Database**: SQLite (default, configurable for PostgreSQL/MySQL)
- **Frontend**: HTML, CSS (Tailwind CSS), JavaScript
- **Payment Gateway**: Razorpay
- **PDF Generation**: ReportLab
- **Authentication**: OTP (One-Time Password)

## License

This project is proprietary to Tradersfy.

## Version

**Tradersfy LMS v1.0.0**

Last Updated: June 2026
