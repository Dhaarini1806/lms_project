from django.urls import path
from django.contrib import admin
from .views import (
    home_view,
    login_view,
    front_end_logout,
    send_otp,
    verify_otp,
    course_catalog,
    course_detail,
    lesson_detail,
    add_to_cart,
    view_cart,
    checkout_view,
    remove_from_cart,
    toggle_wishlist,
    verify_payment,
    order_success,
    profile_view,
    stream_video,
)

from .admin_views import (
    admin_dashboard,
    admin_courses,
    admin_add_course,
    admin_edit_course,
    admin_delete_course,
    admin_users,
    admin_user_detail,
    admin_add_user,
    admin_groups,
    admin_add_group,
    admin_download_users_pdf,
    admin_transactions,
    admin_transaction_detail,
    admin_download_transactions_pdf,
    admin_analytics,
    admin_activity,
    admin_dashboard,
    update_lesson_order,
    admin_testimonials,
    admin_delete_testimonial,
)

from .invoice_views import (
    invoice_page,
    download_invoice_pdf,
    certificate_page,
    download_certificate_pdf,
)

urlpatterns = [
    # Public Routes
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', front_end_logout, name='logout'),
    path('admin/', admin.site.urls),
    
    # Authentication
    path('send-otp/', send_otp, name='send_otp'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    # API endpoints for frontend AJAX calls
    path('api/auth/send-otp/', send_otp, name='api_send_otp'),
    path('api/auth/verify-otp/', verify_otp, name='api_verify_otp'),
    
    # Catalog & Courses
    path('courses/', course_catalog, name='course_catalog'),
    path('courses/<slug:course_slug>/', course_detail, name='course_detail'),
    path('courses/<slug:course_slug>/lessons/<slug:lesson_slug>/', lesson_detail, name='lesson_detail'),
    
    # Cart & Checkout
    path('cart/add/<int:course_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', view_cart, name='view_cart'),
    path('cart/remove/<int:course_id>/', remove_from_cart, name='remove_from_cart'),
    path('wishlist/toggle/<int:course_id>/', toggle_wishlist, name='toggle_wishlist'),
    path('checkout/', checkout_view, name='checkout'),
    path('checkout/verify-payment/', verify_payment, name='verify_payment'),
    path('checkout/success/<int:order_id>/', order_success, name='order_success'),
    path('invoice/<int:order_id>/', invoice_page, name='invoice_page'),
    path('invoice/<int:order_id>/download/', download_invoice_pdf, name='download_invoice_pdf'),
    path('certificate/<int:course_id>/', certificate_page, name='certificate_page'),
    path('certificate/<int:certificate_id>/download/', download_certificate_pdf, name='download_certificate_pdf'),
    
    # User Profile
    path('profile/', profile_view, name='profile'),
    
    # Custom Admin Panel
    path('master/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('master/courses/', admin_courses, name='admin_courses'),
    path('master/add-course/', admin_add_course, name='admin_add_course'),
    path('master/edit-course/<int:course_id>/', admin_edit_course, name='admin_edit_course'),
    path('master/delete-course/<int:course_id>/', admin_delete_course, name='admin_delete_course'),
    path('master/users/', admin_users, name='admin_users'),
    path('master/users/add/', admin_add_user, name='admin_add_user'),
    path('master/groups/', admin_groups, name='admin_groups'),
    path('master/groups/add/', admin_add_group, name='admin_add_group'),
    path('master/user/<int:user_id>/', admin_user_detail, name='admin_user_detail'),
    path('master/download-users-pdf/', admin_download_users_pdf, name='admin_download_users_pdf'),
    path('master/transactions/', admin_transactions, name='admin_transactions'),
    path('master/transaction/<int:order_id>/', admin_transaction_detail, name='admin_transaction_detail'),
    path('master/download-transactions-pdf/', admin_download_transactions_pdf, name='admin_download_transactions_pdf'),
    path('master/analytics/', admin_analytics, name='admin_analytics'),
    path('master/activity/', admin_activity, name='admin_activity'),
    path('master/update-lesson-order/', update_lesson_order, name='update_lesson_order'),
    path('master/testimonials/', admin_testimonials, name='admin_testimonials'),
    path('master/delete-testimonial/<int:testimonial_id>/', admin_delete_testimonial, name='admin_delete_testimonial'),
    path('stream-video/<int:lesson_id>/', stream_video, name='stream_video'),
    
    # Lesson Player
    path('courses/<slug:course_slug>/lessons/<slug:lesson_slug>/player/', lesson_detail, name='lesson_player'),
    path('api/stream-video/<int:lesson_id>/', stream_video, name='api_stream_video'),
]