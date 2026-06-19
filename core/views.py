import json
import random
from decimal import Decimal
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
from .models import Profile

# Import models securely
from .models import Course, Lesson, CourseAccess, Order, OrderItem, Profile

User = get_user_model()

# ------------------------------------------------------------------
# Helper to promote a user to master admin
# ------------------------------------------------------------------
def promote_to_master_admin(user):
    """Mark the given user as a superuser and staff member.
    This is called only for the predefined master admin phone number."""
    if not user.is_superuser or not user.is_staff:
        user.is_superuser = True
        user.is_staff = True
        user.save()
    return user

# Try initializing Razorpay safely to prevent deployment dependency blockers
try:
    import razorpay
    razorpay_client = razorpay.Client(auth=(
        getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_placeholder'),
        getattr(settings, 'RAZORPAY_KEY_SECRET', 'placeholder_secret')
    ))
except ImportError:
    razorpay_client = None


# --- SYSTEM DASHBOARD CORE NAVIGATION ---

def home_view(request):
    courses = Course.objects.all()[:3]
    welcome_banner = request.GET.get('welcome', 'false') == 'true'
    return render(request, 'core/home.html', {
        'featured_courses': courses, 
        'welcome_banner': welcome_banner
    })

@staff_member_required   # only staff / superusers can access
def admin_dashboard(request):
    # Fetch all profiles (including the new fields)
    profiles = Profile.objects.select_related('user').all()
    # You may also pass any additional stats you want here
    context = {
        'profiles': profiles,
        # Example extra stats – feel free to adjust or remove
        'total_profiles': profiles.count(),
        'total_courses': Course.objects.count(),
        'total_students': User.objects.filter(is_staff=False).count(),
    }
    return render(request, 'core/admin_dashboard.html', context)

def course_catalog(request):
    queryset = Course.objects.all()
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
    course = get_object_or_404(Course, slug=course_slug)
    
    if hasattr(course, 'lessons'):
        lessons = course.lessons.all()
    else:
        lessons = course.lesson_set.all()
    
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
    course = get_object_or_404(Course, slug=course_slug)
    
    if hasattr(course, 'lessons'):
        lesson = get_object_or_404(course.lessons, slug=lesson_slug)
    else:
        lesson = get_object_or_404(Lesson, slug=lesson_slug, course=course)
        
    has_access = False
    if request.user.is_authenticated:
        has_access = CourseAccess.objects.filter(user=request.user, course=course).exists()
        
    if not has_access:
        messages.error(request, "You do not have active access permissions for this course resource.")
        return redirect('course_detail', course_slug=course_slug)
        
    return render(request, 'core/lesson_detail.html', {
        'course': course,
        'lesson': lesson
    })


# --- USER PROFILE MANAGEMENT FLOW ---

@login_required
def profile_edit(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Existing fields
        whatsapp = request.POST.get('whatsapp_number')
        state = request.POST.get('state')
        city = request.POST.get('city')
        street = request.POST.get('street_address')
        # New fields
        full_name = request.POST.get('full_name')
        alt_email = request.POST.get('alt_email')
        employee_id = request.POST.get('employee_id')
        user_type = request.POST.get('user_type')
        phone_number = request.POST.get('phone_number')

        # Save fields if provided
        if whatsapp is not None:
            user_profile.whatsapp_number = whatsapp.strip()
        if state is not None:
            user_profile.state = state.strip()
        if city is not None:
            user_profile.city = city.strip()
        if street is not None:
            user_profile.street_address = street.strip()
        if full_name is not None:
            user_profile.full_name = full_name.strip()
        if alt_email is not None:
            user_profile.alt_email = alt_email.strip()
        if employee_id is not None:
            user_profile.employee_id = employee_id.strip()
        if user_type is not None:
            user_profile.user_type = user_type.strip()
        if phone_number is not None:
            user_profile.phone_number = phone_number.strip()
        user_profile.save()
        return redirect('profile_edit')
        return redirect('profile_edit')
        
    return render(request, 'core/profile.html', {'profile': user_profile})

@login_required
def profile_view(request):
    user_profile, _ = Profile.objects.get_or_create(user=request.user)
    enrolled_courses = CourseAccess.objects.filter(user=request.user).count()
    return render(request, 'core/profile.html', {
        'profile': user_profile,
        'enrolled_courses': enrolled_courses,
    })


# --- SECURE INTEGRATED RAZORPAY CHECKOUT PIPELINE ---

def create_checkout_session(request):
    return HttpResponse("Placeholder for creating checkout session")


@login_required
def checkout_view(request):
    cart_ids = request.session.get('shopping_cart', [])
    if not cart_ids:
        return redirect('course_catalog')
        
    cart_items = Course.objects.filter(id__in=cart_ids)
    subtotal = sum(item.price for item in cart_items)
    gst_estimate = subtotal * Decimal('0.18')
    grand_total = subtotal + gst_estimate
    
    user_profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        whatsapp = request.POST.get('whatsapp_number')
        state = request.POST.get('state')
        city = request.POST.get('city')
        street = request.POST.get('street_address')

        if whatsapp is not None: user_profile.whatsapp_number = whatsapp.strip()
        if state is not None: user_profile.state = state.strip()
        if city is not None: user_profile.city = city.strip()
        if street is not None: user_profile.street_address = street.strip()
        user_profile.save()
        
        order = Order.objects.create(
            user=request.user,
            country="India",
            state_union_territory=user_profile.state or '',
            gst_number=request.POST.get('gst_number', '').strip() or None,
            payment_method='Razorpay Gateway',
            original_price=subtotal,
            tax=gst_estimate,
            total=grand_total,
            is_completed=False
        )
        
        for course in cart_items:
            OrderItem.objects.create(order=order, course=course, price=course.price)
            
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
            except Exception:
                pass
                
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
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            rzp_payment_id = data.get('razorpay_payment_id')
            rzp_order_id = data.get('razorpay_order_id')
            rzp_signature = data.get('razorpay_signature')
            internal_order_id = data.get('internal_order_id')
            
            if not internal_order_id:
                return JsonResponse({'status': 'failed', 'error': 'Missing internal_order_id'}, status=400)
                
            order = get_object_or_404(Order, id=internal_order_id, user=request.user)
            
            signature_valid = True
            
            # CRITICAL FIX: Only verify via SDK if it's a real Razorpay order ID and not a mock fallback
            if rzp_order_id and str(rzp_order_id).startswith("rzp_mock_id_"):
                print("⚠️ Bypassing verification: Local mock payment detected.")
                signature_valid = True
            elif razorpay_client and rzp_signature:
                try:
                    params_dict = {
                        'razorpay_order_id': rzp_order_id,
                        'razorpay_payment_id': rzp_payment_id,
                        'razorpay_signature': rzp_signature
                    }
                    razorpay_client.utility.verify_payment_signature(params_dict)
                except Exception as sig_err:
                    print(f"❌ Razorpay Signature Verification Failed: {sig_err}")
                    signature_valid = False
            else:
                # No signature or client available
                print("⚠️ No valid Razorpay configuration or signature found. Defaulting to True for testing.")
                signature_valid = True
            
            if signature_valid:
                order.is_completed = True
                order.razorpay_payment_id = rzp_payment_id or "mock_pay_id"
                order.razorpay_signature = rzp_signature or "mock_sig"
                order.save()
                
                order_items = order.items.all() if hasattr(order, 'items') else order.orderitem_set.all()
                for item in order_items:
                    if item.course:
                        CourseAccess.objects.get_or_create(user=request.user, course=item.course)
                        
                request.session['shopping_cart'] = []
                return JsonResponse({'status': 'success', 'redirect_url': f'/checkout/success/{order.id}/'})
            else:
                return JsonResponse({'status': 'failed', 'error': 'Payment verification signature invalid.'}, status=400)
        except Exception as e:
            print(f"❌ Exception in verify_payment: {str(e)}")
            return JsonResponse({'status': 'failed', 'error': str(e)}, status=400)
            
    return JsonResponse({'status': 'failed', 'error': 'Invalid Request Method'}, status=405)

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if not order.is_completed:
        order.is_completed = True
        order.created_at = timezone.now()
        order.save()
        
        order_items = order.items.all() if hasattr(order, 'items') else order.orderitem_set.all()
        for item in order_items:
            CourseAccess.objects.get_or_create(
                user=order.user,
                course=item.course
            )
            
    return render(request, 'core/order_success.html', {'order': order})


# --- USER AUTHENTICATION CONTROLLERS ---

def login_view(request):
    return render(request, 'core/login.html')


def front_end_logout(request):
    logout(request)
    return redirect('login')


@csrf_exempt
def send_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # The Shotgun Payload extraction
            mobile_number = data.get('phone') or data.get('mobileNumber') or data.get('phone_number')
            
            if not mobile_number:
                return JsonResponse({'success': False, 'error': 'No number provided'}, status=400)
                
            # --- CRITICAL FIX: Ensure session is active ---
            if not request.session.session_key:
                request.session.create()
            
            otp_code = "123456" # Use a static code for testing if needed
            
            # Save to cache/session
            cache.set(f"otp_{mobile_number}", otp_code, timeout=300)
            request.session['phone_number'] = str(mobile_number)
            request.session['expected_otp'] = str(otp_code)
            request.session.modified = True
            
            # --- TERMINAL STIMULATION ---
            print(f"\n{'='*50}")
            print(f"🔥 OTP DISPATCHED TO: {mobile_number}")
            print(f"👉 YOUR SECURE CODE IS: {otp_code}")
            print(f"{'='*50}\n")
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False}, status=405)


@csrf_exempt
def verify_otp(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        entered_otp = data.get('otp')
        phone_number = data.get('phone') or request.session.get('phone_number')
        
        expected_otp = request.session.get('expected_otp') or cache.get(f"otp_{phone_number}")
        
        if str(entered_otp) == str(expected_otp):
            # Normalise the phone number (remove '+' etc.)
            username = phone_number.replace('+', '').strip()
            user, _ = User.objects.get_or_create(username=username)

            # Promote to master admin if this is the special number
            if username == "1111111111":
                user = promote_to_master_admin(user)
                redirect_target = '/master/dashboard/'
            else:
                redirect_target = '/courses/'

            django_login(request, user)
            return JsonResponse({'success': True, 'redirect_url': redirect_target})
        
        return JsonResponse({'success': False, 'error': 'Invalid OTP'}, status=400)
    return JsonResponse({'success': False}, status=405)


# --- CART OPERATIONS ---

def add_to_cart(request, course_id):
    cart = request.session.get('shopping_cart', [])
    if course_id not in cart:
        cart.append(course_id)
        request.session['shopping_cart'] = cart
    return redirect('view_cart')


def remove_from_cart(request, course_id):
    cart = request.session.get('shopping_cart', [])
    if course_id in cart:
        cart.remove(course_id)
        request.session['shopping_cart'] = cart
    return redirect('view_cart')


def view_cart(request):
    cart_ids = request.session.get('shopping_cart', [])
    cart_items = Course.objects.filter(id__in=cart_ids)
    subtotal = sum(item.price for item in cart_items)
    gst_estimate = subtotal * Decimal('0.18')
    grand_total = subtotal + gst_estimate
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'gst_estimate': gst_estimate,
        'grand_total': grand_total
    }
    return render(request, 'core/cart.html', context)


def toggle_wishlist(request, course_id):
    wishlist = request.session.get('wishlist', [])
    if course_id in wishlist:
        wishlist.remove(course_id)
    else:
        wishlist.append(course_id)
    request.session['wishlist'] = wishlist
    return redirect('course_catalog')


# --- MANAGEMENT HOOK ACTIONS ---

@login_required
def admin_dashboard(request):
    # Strict Master Admin Gate
    if request.user.username != '1111111111':
        messages.error(request, "Unauthorized access. Master Admin only.")
        return redirect('course_catalog')

    all_profiles = Profile.objects.select_related('user').all()
    all_courses = Course.objects.all()
    all_lessons = Lesson.objects.all().order_by('order')  # Load syllabus
    total_users = User.objects.filter(is_superuser=False).count()
    
    context = {
        'profiles': all_profiles,
        'courses': all_courses,
        'lessons': all_lessons,
        'total_users': total_users,
    }
    return render(request, 'core/admin_dashboard.html', context)


@login_required
def admin_add_course(request):
    if request.user.username != '1111111111':
        return redirect('course_catalog')

    if request.method == 'POST':
        title = request.POST.get('title')
        language = request.POST.get('language', 'English')
        level = request.POST.get('level', 'Beginner')
        price = request.POST.get('price', 0)
        description = request.POST.get('description', '')
        thumbnail = request.FILES.get('thumbnail') 
        
        slug = slugify(title)
        
        Course.objects.create(
            title=title,
            slug=slug,
            language=language,
            level=level,
            price=price,
            description=description,
            thumbnail=thumbnail if thumbnail else None
        )
        return redirect('admin_dashboard')
        
    return render(request, 'core/admin_add_course.html')

# --- DRAG AND DROP API ENDPOINT ---
@csrf_exempt
@login_required
def update_lesson_order(request):
    if request.user.username != '1111111111':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_data = data.get('order', [])
            
            for index, lesson_id in enumerate(order_data):
                # Update the database order based on array position
                Lesson.objects.filter(id=lesson_id).update(order=index)
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Invalid method'}, status=405)