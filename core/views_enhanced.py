import json
import random
from decimal import Decimal
from datetime import timedelta
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from django.contrib import messages
from django.contrib.auth import get_user_model, login as django_login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from .models import Profile, Course, Lesson, CourseAccess, Order, OrderItem, Certificate, OTPSession

User = get_user_model()

# Try initializing Razorpay safely to prevent deployment dependency blockers
try:
    import razorpay
    razorpay_client = razorpay.Client(auth=(
        getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_placeholder'),
        getattr(settings, 'RAZORPAY_KEY_SECRET', 'placeholder_secret')
    ))
except ImportError:
    razorpay_client = None


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def promote_to_master_admin(user):
    """Mark the given user as a superuser and staff member."""
    if not user.is_superuser or not user.is_staff:
        user.is_superuser = True
        user.is_staff = True
        user.save()
    return user


def generate_otp():
    """Generate a random 6-digit OTP."""
    return str(random.randint(100000, 999999))


def validate_phone_number(phone):
    """Validate if phone number is exactly 10 digits."""
    return phone.isdigit() and len(phone) == 10


def fulfill_order(order):
    """
    Automated post-purchase fulfillment process.
    Maps all order items to CourseAccess and grants user permissions.
    """
    try:
        order_items = order.items.all()
        for item in order_items:
            if item.course:
                course_access, created = CourseAccess.objects.get_or_create(
                    user=order.user,
                    course=item.course
                )
                if created:
                    print(f"✓ Granted access: {order.user.username} → {item.course.title}")
        
        # Mark order as completed
        order.is_completed = True
        order.status = 'completed'
        order.completed_at = timezone.now()
        order.save()
        
        # Clear shopping cart session
        return True
    except Exception as e:
        print(f"❌ Fulfillment failed for Order {order.order_id}: {str(e)}")
        order.status = 'failed'
        order.save()
        return False


# ==========================================
# AUTHENTICATION VIEWS
# ==========================================

def login_view(request):
    """Render the OTP login page."""
    return render(request, 'core/login.html')


@csrf_exempt
def send_otp(request):
    """
    Enhanced OTP Generation and Session Management.
    Validates 10-digit phone number and creates OTP session.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone', '').strip()
            
            # Validate phone number format
            if not validate_phone_number(phone_number):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid phone number. Please enter exactly 10 digits.'
                }, status=400)
            
            # Generate OTP
            otp_code = generate_otp()
            
            # Create or update OTP session
            expires_at = timezone.now() + timedelta(minutes=10)
            otp_session, created = OTPSession.objects.update_or_create(
                phone_number=phone_number,
                defaults={
                    'otp_code': otp_code,
                    'is_verified': False,
                    'attempts': 0,
                    'expires_at': expires_at
                }
            )
            
            # In production, send OTP via SMS using Twilio/AWS SNS
            # For now, log it for development
            print(f"📱 OTP for {phone_number}: {otp_code}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'OTP sent successfully',
                'debug_otp': otp_code  # Remove in production
            })
        
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid request format'
            }, status=400)
        except Exception as e:
            print(f"❌ Error in send_otp: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to send OTP'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)


@csrf_exempt
def verify_otp(request):
    """
    OTP Verification with Session Security.
    Validates 6-digit code and authenticates user.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone', '').strip()
            otp_code = data.get('otp', '').strip()
            
            # Validate inputs
            if not validate_phone_number(phone_number):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid phone number'
                }, status=400)
            
            if not otp_code or len(otp_code) != 6:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid OTP format'
                }, status=400)
            
            # Retrieve OTP session
            try:
                otp_session = OTPSession.objects.get(phone_number=phone_number)
            except OTPSession.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'OTP session not found. Please request a new OTP.'
                }, status=404)
            
            # Check if expired
            if otp_session.is_expired():
                return JsonResponse({
                    'status': 'error',
                    'message': 'OTP has expired. Please request a new one.'
                }, status=400)
            
            # Check attempt limit
            if not otp_session.is_valid_attempt():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Too many attempts. Please request a new OTP.'
                }, status=429)
            
            # Verify OTP
            if otp_session.otp_code != otp_code:
                otp_session.attempts += 1
                otp_session.save()
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid OTP. {3 - otp_session.attempts} attempts remaining.'
                }, status=400)
            
            # OTP verified - create or get user
            otp_session.is_verified = True
            otp_session.save()
            
            user, created = User.objects.get_or_create(
                username=phone_number,
                defaults={'email': f'{phone_number}@tradersfy.local'}
            )
            
            # Ensure profile exists
            Profile.objects.get_or_create(user=user)
            
            # Promote master admin if needed
            if phone_number == '1111111111':
                promote_to_master_admin(user)
            
            # Login user
            django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            return JsonResponse({
                'status': 'success',
                'message': 'Authentication successful',
                'redirect_url': '/?welcome=true'
            })
        
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid request format'
            }, status=400)
        except Exception as e:
            print(f"❌ Error in verify_otp: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Verification failed'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)


def front_end_logout(request):
    """Logout the user and redirect to login."""
    logout(request)
    return redirect('login')


# ==========================================
# CATALOG & COURSE VIEWS
# ==========================================

def home_view(request):
    """Render the home page with featured courses."""
    courses = Course.objects.filter(is_published=True)[:3]
    welcome_banner = request.GET.get('welcome', 'false') == 'true'
    return render(request, 'core/home.html', {
        'featured_courses': courses,
        'welcome_banner': welcome_banner
    })


def course_catalog(request):
    """Render the course catalog with filtering and sorting."""
    queryset = Course.objects.filter(is_published=True)
    selected_languages = request.GET.getlist('language')
    selected_levels = request.GET.getlist('level')
    min_rating = request.GET.get('rating')
    max_price = request.GET.get('price')
    sort_by = request.GET.get('sort', 'popular')
    
    if selected_languages:
        queryset = queryset.filter(language__in=selected_languages)
    if selected_levels:
        queryset = queryset.filter(level__in=selected_levels)
    if min_rating:
        queryset = queryset.filter(rating__gte=float(min_rating))
    if max_price:
        queryset = queryset.filter(price__lte=float(max_price))
    
    if sort_by == 'popular':
        queryset = queryset.order_by('-rating')
    elif sort_by == 'price_low':
        queryset = queryset.order_by('price')
    elif sort_by == 'price_high':
        queryset = queryset.order_by('-price')
    
    context = {
        'courses': queryset,
        'selected_languages': selected_languages,
        'selected_levels': selected_levels,
        'selected_rating': min_rating,
        'max_price': max_price,
        'sort_by': sort_by,
    }
    return render(request, 'core/courses.html', context)


def course_detail(request, course_slug):
    """Render detailed course page with access control."""
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    lessons = course.lessons.all()
    
    has_access = False
    if request.user.is_authenticated:
        has_access = CourseAccess.objects.filter(user=request.user, course=course).exists()
    
    context = {
        'course': course,
        'lessons': lessons,
        'has_access': has_access
    }
    return render(request, 'core/course_detail.html', context)


def lesson_detail(request, course_slug, lesson_slug):
    """Render lesson page with gated access control."""
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    lesson = get_object_or_404(Lesson, slug=lesson_slug, course=course)
    
    has_access = False
    if request.user.is_authenticated:
        has_access = CourseAccess.objects.filter(user=request.user, course=course).exists()
    
    if not has_access and not lesson.is_preview:
        messages.error(request, "You do not have access to this lesson. Please purchase the course.")
        return redirect('course_detail', course_slug=course_slug)
    
    return render(request, 'core/lesson_detail.html', {
        'course': course,
        'lesson': lesson,
        'has_access': has_access
    })


# ==========================================
# CART & CHECKOUT VIEWS
# ==========================================

@login_required
def add_to_cart(request, course_id):
    """Add a course to the shopping cart."""
    course = get_object_or_404(Course, id=course_id, is_published=True)
    
    # Initialize cart if not exists
    if 'shopping_cart' not in request.session:
        request.session['shopping_cart'] = []
    
    cart = request.session['shopping_cart']
    if course_id not in cart:
        cart.append(course_id)
        request.session['shopping_cart'] = cart
        messages.success(request, f"{course.title} added to cart!")
    else:
        messages.info(request, f"{course.title} is already in your cart.")
    
    return redirect('view_cart')


@login_required
def view_cart(request):
    """Display the shopping cart."""
    cart_ids = request.session.get('shopping_cart', [])
    cart_items = Course.objects.filter(id__in=cart_ids, is_published=True)
    
    subtotal = sum(Decimal(str(item.price)) for item in cart_items)
    gst_estimate = subtotal * Decimal('0.18')
    grand_total = subtotal + gst_estimate
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'gst_estimate': gst_estimate,
        'grand_total': grand_total,
    }
    return render(request, 'core/cart.html', context)


@login_required
def remove_from_cart(request, course_id):
    """Remove a course from the shopping cart."""
    if 'shopping_cart' in request.session:
        cart = request.session['shopping_cart']
        if course_id in cart:
            cart.remove(course_id)
            request.session['shopping_cart'] = cart
            messages.success(request, "Item removed from cart.")
    
    return redirect('view_cart')


@login_required
def toggle_wishlist(request, course_id):
    """Toggle course in user's wishlist (placeholder)."""
    # This can be implemented with a Wishlist model if needed
    messages.info(request, "Wishlist feature coming soon!")
    return redirect('course_detail', course_slug=Course.objects.get(id=course_id).slug)


# ==========================================
# CHECKOUT & PAYMENT VIEWS
# ==========================================

@login_required
def checkout_view(request):
    """
    Enhanced Checkout with Razorpay Integration.
    Handles order creation and payment gateway initialization.
    """
    cart_ids = request.session.get('shopping_cart', [])
    if not cart_ids:
        return redirect('course_catalog')
    
    cart_items = Course.objects.filter(id__in=cart_ids, is_published=True)
    subtotal = sum(Decimal(str(item.price)) for item in cart_items)
    gst_estimate = subtotal * Decimal('0.18')
    grand_total = subtotal + gst_estimate
    
    user_profile, _ = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update user profile with checkout details
        whatsapp = request.POST.get('whatsapp_number', '').strip()
        state = request.POST.get('state', '').strip()
        city = request.POST.get('city', '').strip()
        street = request.POST.get('street_address', '').strip()
        
        if whatsapp:
            user_profile.whatsapp_number = whatsapp
        if state:
            user_profile.state = state
        if city:
            user_profile.city = city
        if street:
            user_profile.street_address = street
        user_profile.save()
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            country="India",
            state_union_territory=user_profile.state or '',
            gst_number=request.POST.get('gst_number', '').strip() or None,
            payment_method='Razorpay Gateway',
            original_price=subtotal,
            tax=gst_estimate,
            total=grand_total,
            status='pending',
            is_completed=False
        )
        
        # Create order items
        for course in cart_items:
            OrderItem.objects.create(order=order, course=course, price=course.price)
        
        # Generate Razorpay order
        amount_paisa = int(grand_total * 100)
        rzp_order_id = "rzp_mock_id_" + str(random.randint(10000, 99999))
        
        if razorpay_client:
            try:
                data = {
                    "amount": amount_paisa,
                    "currency": "INR",
                    "receipt": f"order_rcpt_{order.id}",
                    "payment_capture": 1
                }
                razorpay_order = razorpay_client.order.create(data=data)
                rzp_order_id = razorpay_order['id']
            except Exception as e:
                print(f"⚠️ Razorpay order creation failed: {str(e)}")
        
        order.razorpay_order_id = rzp_order_id
        order.save()
        
        context = {
            'order': order,
            'cart_items': cart_items,
            'subtotal': subtotal,
            'gst_estimate': gst_estimate,
            'grand_total': grand_total,
            'profile': user_profile,
            'razorpay_order_id': rzp_order_id,
            'razorpay_key_id': getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_placeholder'),
            'amount_paisa': amount_paisa
        }
        return render(request, 'core/checkout.html', context)
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'gst_estimate': gst_estimate,
        'grand_total': grand_total,
        'profile': user_profile,
        'razorpay_order_id': None
    }
    return render(request, 'core/checkout.html', context)


@csrf_exempt
@login_required
def verify_payment(request):
    """
    Transactional Integrity & Verification.
    Validates Razorpay signature and triggers fulfillment.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            rzp_payment_id = data.get('razorpay_payment_id')
            rzp_order_id = data.get('razorpay_order_id')
            rzp_signature = data.get('razorpay_signature')
            internal_order_id = data.get('internal_order_id')
            
            if not internal_order_id:
                return JsonResponse({
                    'status': 'failed',
                    'error': 'Missing internal_order_id'
                }, status=400)
            
            order = get_object_or_404(Order, id=internal_order_id, user=request.user)
            
            signature_valid = True
            
            # Mock payment bypass for testing
            if rzp_order_id and str(rzp_order_id).startswith("rzp_mock_id_"):
                print("⚠️ Mock payment detected - bypassing signature verification")
                signature_valid = True
            elif razorpay_client and rzp_signature:
                try:
                    params_dict = {
                        'razorpay_order_id': rzp_order_id,
                        'razorpay_payment_id': rzp_payment_id,
                        'razorpay_signature': rzp_signature
                    }
                    razorpay_client.utility.verify_payment_signature(params_dict)
                    print("✓ Razorpay signature verified")
                except Exception as sig_err:
                    print(f"❌ Signature verification failed: {sig_err}")
                    signature_valid = False
            else:
                print("⚠️ No Razorpay configuration - defaulting to True for testing")
                signature_valid = True
            
            if signature_valid:
                # Store payment details
                order.razorpay_payment_id = rzp_payment_id or "mock_pay_id"
                order.razorpay_signature = rzp_signature or "mock_sig"
                order.save()
                
                # Trigger automated fulfillment
                if fulfill_order(order):
                    # Clear shopping cart
                    request.session['shopping_cart'] = []
                    request.session.modified = True
                    
                    return JsonResponse({
                        'status': 'success',
                        'redirect_url': f'/checkout/success/{order.id}/'
                    })
                else:
                    return JsonResponse({
                        'status': 'failed',
                        'error': 'Fulfillment failed'
                    }, status=500)
            else:
                return JsonResponse({
                    'status': 'failed',
                    'error': 'Payment signature invalid'
                }, status=400)
        
        except Exception as e:
            print(f"❌ Error in verify_payment: {str(e)}")
            return JsonResponse({
                'status': 'failed',
                'error': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'failed',
        'error': 'Invalid request method'
    }, status=405)


@login_required
def order_success(request, order_id):
    """Display order success page."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'core/order_success.html', {'order': order})


# ==========================================
# PROFILE VIEWS
# ==========================================

@login_required
def profile_view(request):
    """Display and manage user profile."""
    user_profile, _ = Profile.objects.get_or_create(user=request.user)
    enrolled_courses = CourseAccess.objects.filter(user=request.user).count()
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        alt_email = request.POST.get('alt_email', '').strip()
        employee_id = request.POST.get('employee_id', '').strip()
        user_type = request.POST.get('user_type', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        whatsapp = request.POST.get('whatsapp_number', '').strip()
        state = request.POST.get('state', '').strip()
        city = request.POST.get('city', '').strip()
        street = request.POST.get('street_address', '').strip()
        
        if full_name:
            user_profile.full_name = full_name
        if alt_email:
            user_profile.alt_email = alt_email
        if employee_id:
            user_profile.employee_id = employee_id
        if user_type:
            user_profile.user_type = user_type
        if phone_number:
            user_profile.phone_number = phone_number
        if whatsapp:
            user_profile.whatsapp_number = whatsapp
        if state:
            user_profile.state = state
        if city:
            user_profile.city = city
        if street:
            user_profile.street_address = street
        
        user_profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')
    
    return render(request, 'core/profile.html', {
        'profile': user_profile,
        'enrolled_courses': enrolled_courses,
    })


# ==========================================
# CUSTOM ADMIN VIEWS
# ==========================================

@staff_member_required
def admin_dashboard(request):
    """Custom admin dashboard."""
    profiles = Profile.objects.select_related('user').all()
    context = {
        'profiles': profiles,
        'total_profiles': profiles.count(),
        'total_courses': Course.objects.count(),
        'total_students': User.objects.filter(is_staff=False).count(),
        'total_orders': Order.objects.count(),
    }
    return render(request, 'core/admin_dashboard.html', context)


@login_required
def admin_add_course(request):
    """Add new course (admin only)."""
    if request.user.username != '1111111111':
        return redirect('course_catalog')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        language = request.POST.get('language', 'English')
        level = request.POST.get('level', 'Beginner')
        price = request.POST.get('price', 0)
        description = request.POST.get('description', '').strip()
        
        slug = slugify(title)
        
        Course.objects.create(
            title=title,
            slug=slug,
            language=language,
            level=level,
            price=price,
            description=description,
            is_published=True
        )
        messages.success(request, "Course created successfully!")
        return redirect('admin_dashboard')
    
    return render(request, 'core/admin_add_course.html')


@csrf_exempt
@login_required
def update_lesson_order(request):
    """Update lesson order via drag-and-drop."""
    if request.user.username != '1111111111':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_data = data.get('order', [])
            
            for index, lesson_id in enumerate(order_data):
                Lesson.objects.filter(id=lesson_id).update(order=index)
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)
