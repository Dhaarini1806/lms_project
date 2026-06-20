from django.contrib import admin
from .models import Profile, Course, Lesson, CourseAccess, Order, OrderItem, Certificate, LoginHistory

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'whatsapp_number', 'state', 'city')

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'level', 'price', 'rating')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LessonInline]

@admin.register(CourseAccess)
class CourseAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'unlocked_at')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'total', 'payment_method', 'is_completed', 'created_at')
    list_filter = ('is_completed', 'payment_method')
    inlines = [OrderItemInline]

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_number', 'user', 'course', 'issue_date')

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_at', 'ip_address')
    list_filter = ('login_at',)