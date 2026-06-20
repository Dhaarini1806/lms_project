"""
Custom Admin Panel Views for Tradersfy
Handles admin dashboard, user management, course management, and transaction reporting
"""

import json
from datetime import datetime
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt

from .models import Profile, Course, Lesson, Order, OrderItem, CourseAccess, Certificate

# PDF Generation Libraries
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def is_master_admin(user):
    """Check if user is the master admin."""
    return user.username == '1111111111' and user.is_superuser


def get_admin_stats():
    """Get dashboard statistics."""
    return {
        'total_users': User.objects.filter(is_staff=False).count(),
        'total_courses': Course.objects.count(),
        'total_orders': Order.objects.count(),
        'completed_orders': Order.objects.filter(is_completed=True).count(),
        'total_revenue': Order.objects.filter(is_completed=True).aggregate(Sum('total'))['total__sum'] or Decimal('0.00'),
        'pending_orders': Order.objects.filter(status='pending').count(),
    }


def generate_transaction_pdf(transactions):
    """Generate PDF for transactions."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e1e1e'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Title
    title = Paragraph("Transaction Report - Tradersfy", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Report Date
    date_style = ParagraphStyle('DateStyle', parent=styles['Normal'], fontSize=10, textColor=colors.grey)
    date_para = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style)
    elements.append(date_para)
    elements.append(Spacer(1, 0.2 * inch))
    
    # Table Data
    table_data = [['Order ID', 'User', 'Total Amount', 'Status', 'Date']]
    
    for order in transactions:
        table_data.append([
            order.order_id,
            order.user.username,
            f"₹{order.total}",
            order.status.upper(),
            order.created_at.strftime('%Y-%m-%d')
        ])
    
    # Create Table
    table = Table(table_data, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 1.2*inch, 1.3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e1e1e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.5 * inch))
    
    # Summary
    total_revenue = sum(Decimal(str(order.total)) for order in transactions)
    summary_style = ParagraphStyle('Summary', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#1e1e1e'), spaceAfter=6)
    elements.append(Paragraph(f"<b>Total Transactions:</b> {len(transactions)}", summary_style))
    elements.append(Paragraph(f"<b>Total Revenue:</b> ₹{total_revenue}", summary_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_user_pdf(users):
    """Generate PDF for user details."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e1e1e'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Title
    title = Paragraph("User Details Report - Tradersfy", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Report Date
    date_style = ParagraphStyle('DateStyle', parent=styles['Normal'], fontSize=10, textColor=colors.grey)
    date_para = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style)
    elements.append(date_para)
    elements.append(Spacer(1, 0.2 * inch))
    
    # Table Data
    table_data = [['Username', 'Full Name', 'Email', 'Phone', 'User Type', 'Joined']]
    
    for user in users:
        profile = getattr(user, 'profile', None)
        table_data.append([
            user.username,
            profile.full_name if profile else 'N/A',
            user.email,
            profile.phone_number if profile else 'N/A',
            profile.get_user_type_display() if profile else 'N/A',
            user.date_joined.strftime('%Y-%m-%d')
        ])
    
    # Create Table
    table = Table(table_data, colWidths=[1*inch, 1.2*inch, 1.3*inch, 1*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e1e1e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.5 * inch))
    
    # Summary
    summary_style = ParagraphStyle('Summary', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#1e1e1e'), spaceAfter=6)
    elements.append(Paragraph(f"<b>Total Users:</b> {len(users)}", summary_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==========================================
# ADMIN DASHBOARD VIEWS
# ==========================================

@login_required
def admin_dashboard(request):
    """Main admin dashboard with statistics and quick actions."""
    if not is_master_admin(request.user):
        messages.error(request, "Unauthorized access")
        return redirect('home')
    
    stats = get_admin_stats()
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    context = {
        'stats': stats,
        'recent_orders': recent_orders,
    }
    return render(request, 'core/admin/dashboard.html', context)


# ==========================================
# COURSE MANAGEMENT
# ==========================================

@login_required
def admin_courses(request):
    """View and manage all courses."""
    if not is_master_admin(request.user):
        return redirect('home')
    
    courses = Course.objects.all()
    context = {'courses': courses}
    return render(request, 'core/admin/courses.html', context)


@login_required
def admin_add_course(request):
    """Add a new course."""
    if not is_master_admin(request.user):
        return redirect('home')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        language = request.POST.get('language', 'English')
        level = request.POST.get('level', 'Beginner')
        price = request.POST.get('price', 0)
        description = request.POST.get('description', '').strip()
        author_name = request.POST.get('author_name', 'Kevin Marks').strip()
        
        slug = slugify(title)
        
        course = Course.objects.create(
            title=title,
            slug=slug,
            language=language,
            level=level,
            price=price,
            description=description,
            author_name=author_name,
            is_published=True
        )
        messages.success(request, f"Course '{title}' created successfully!")
        return redirect('admin_courses')
    
    return render(request, 'core/admin/add_course.html')


@login_required
def admin_edit_course(request, course_id):
    """Edit an existing course."""
    if not is_master_admin(request.user):
        return redirect('home')
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        course.title = request.POST.get('title', course.title).strip()
        course.language = request.POST.get('language', course.language)
        course.level = request.POST.get('level', course.level)
        course.price = request.POST.get('price', course.price)
        course.description = request.POST.get('description', course.description).strip()
        course.author_name = request.POST.get('author_name', course.author_name).strip()
        course.is_published = request.POST.get('is_published') == 'on'
        course.save()
        
        messages.success(request, "Course updated successfully!")
        return redirect('admin_courses')
    
    context = {'course': course}
    return render(request, 'core/admin/edit_course.html', context)


@login_required
def admin_delete_course(request, course_id):
    """Delete a course."""
    if not is_master_admin(request.user):
        return redirect('home')
    
    course = get_object_or_404(Course, id=course_id)
    course_title = course.title
    course.delete()
    messages.success(request, f"Course '{course_title}' deleted successfully!")
    return redirect('admin_courses')


# ==========================================
# USER MANAGEMENT
# ==========================================

@login_required
def admin_users(request):
    """View and manage all users."""
    if not is_master_admin(request.user):
        return redirect('home')
    
    search_query = request.GET.get('search', '')
    users = User.objects.filter(is_staff=False).select_related('profile')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(profile__full_name__icontains=search_query)
        )
    
    context = {
        'users': users,
        'search_query': search_query,
    }
    return render(request, 'core/admin/users.html', context)


@login_required
def admin_user_detail(request, user_id):
    """View detailed user information."""
    if not is_master_admin(request.user):
        return redirect('home')
    
    user = get_object_or_404(User, id=user_id, is_staff=False)
    profile = getattr(user, 'profile', None)
    orders = user.orders.all()
    courses = user.unlocked_courses.all()
    
    context = {
        'user': user,
        'profile': profile,
        'orders': orders,
        'courses': courses,
    }
    return render(request, 'core/admin/user_detail.html', context)


@login_required
def admin_download_users_pdf(request):
    """Download user details as PDF."""
    if not is_master_admin(request.user):
        return redirect('home')
    
    users = User.objects.filter(is_staff=False).select_related('profile')
    pdf_buffer = generate_user_pdf(users)
    
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="users_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    return response


# ==========================================
# TRANSACTION MANAGEMENT
# ==========================================

@login_required
def admin_transactions(request):
    """View all transactions."""
    if not is_master_admin(request.user):
        return redirect('home')
    
    status_filter = request.GET.get('status', '')
    transactions = Order.objects.select_related('user').order_by('-created_at')
    
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    context = {
        'transactions': transactions,
        'status_filter': status_filter,
    }
    return render(request, 'core/admin/transactions.html', context)


@login_required
def admin_transaction_detail(request, order_id):
    """View detailed transaction information."""
    if not is_master_admin(request.user):
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id)
    items = order.items.all()
    
    context = {
        'order': order,
        'items': items,
    }
    return render(request, 'core/admin/transaction_detail.html', context)


@login_required
def admin_download_transactions_pdf(request):
    """Download transactions as PDF."""
    if not is_master_admin(request.user):
        return redirect('home')
    
    status_filter = request.GET.get('status', '')
    transactions = Order.objects.select_related('user').order_by('-created_at')
    
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    pdf_buffer = generate_transaction_pdf(transactions)
    
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="transactions_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    return response


# ==========================================
# ANALYTICS & REPORTS
# ==========================================

@login_required
def admin_analytics(request):
    """View analytics and reports."""
    if not is_master_admin(request.user):
        return redirect('home')
    
    stats = get_admin_stats()
    
    # Course enrollment stats
    course_stats = Course.objects.annotate(
        enrollments=Count('courseaccess')
    ).order_by('-enrollments')[:5]
    
    # Monthly revenue
    monthly_orders = Order.objects.filter(is_completed=True).values('created_at__month').annotate(
        revenue=Sum('total'),
        count=Count('id')
    ).order_by('created_at__month')
    
    context = {
        'stats': stats,
        'course_stats': course_stats,
        'monthly_orders': monthly_orders,
    }
    return render(request, 'core/admin/analytics.html', context)

from django.contrib.auth.models import Group
from django.conf import settings
from .forms import UserForm, ProfileForm, GroupForm

@login_required
def admin_add_user(request):
    """Add a new user and profile."""
    if not is_master_admin(request.user):
        return redirect('home')
    
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()
            
            # Profile is auto-created by signal, but we update it with form data
            profile, created = Profile.objects.get_or_create(user=user)
            for field, value in profile_form.cleaned_data.items():
                setattr(profile, field, value)
            profile.save()
            
            messages.success(request, f"User '{user.username}' created successfully!")
            return redirect('admin_users')
    else:
        user_form = UserForm()
        profile_form = ProfileForm()
    
    return render(request, 'core/admin/add_user.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def admin_groups(request):
    """View and manage groups."""
    if not is_master_admin(request.user):
        return redirect('home')
    
    groups = Group.objects.all().annotate(user_count=Count('user'))
    return render(request, 'core/admin/groups.html', {'groups': groups})

@login_required
def admin_add_group(request):
    """Add a new group."""
    if not is_master_admin(request.user):
        return redirect('home')
    
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Group created successfully!")
            return redirect('admin_groups')
    else:
        form = GroupForm()
    
    return render(request, 'core/admin/add_group.html', {'form': form})

from .models import LoginHistory

@login_required
def admin_activity(request):
    """View user activity: logins and transactions."""
    if not is_master_admin(request.user):
        return redirect('home')
    
    logins = LoginHistory.objects.select_related('user').order_by('-login_at')[:50]
    transactions = Order.objects.select_related('user').order_by('-created_at')[:50]
    
    context = {
        'logins': logins,
        'transactions': transactions,
    }
    return render(request, 'core/admin/activity.html', context)
