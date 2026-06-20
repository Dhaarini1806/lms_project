from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import uuid

# ==========================================
# 1. STUDENT PROFILE SYSTEM
# ==========================================
class Profile(models.Model):
    """
    Extends default user data structures.
    Initializes automatically via safe single-signal routines.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255, blank=True, null=True)
    alt_email = models.EmailField(verbose_name="Alternate Email", blank=True, null=True)
    employee_id = models.CharField(verbose_name="Employee ID", max_length=50, blank=True, null=True)
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('professional', 'Professional'),
        ('instructor', 'Instructor'),
        ('other', 'Other'),
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student')
    phone_number = models.CharField(verbose_name="Phone Number", max_length=20, blank=True, null=True)
    profile_picture_url = models.URLField(verbose_name="Profile Picture URL", blank=True, null=True)
    whatsapp_number = models.CharField(verbose_name="WhatsApp Number", max_length=20, blank=True, null=True)
    state = models.CharField(max_length=100, default="Tamil Nadu", blank=True)
    city = models.CharField(max_length=100, default="Chennai", blank=True)
    street_address = models.TextField(default="Address", blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Profiles"
        ordering = ['-created_at']

    def __str__(self):
        return f"Profile for {self.user.username} ({self.full_name or 'No Name'})"

# Unified Clean Profile Initialization Signal
@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
    else:
        profile, _ = Profile.objects.get_or_create(user=instance)
        profile.save()


# ==========================================
# 2. COURSE & SYLLABUS DATA MODELS
# ==========================================
class Course(models.Model):
    LANGUAGE_CHOICES = [
        ('Tamil', 'Tamil'),
        ('English', 'English'),
        ('Hindi', 'Hindi'),
        ('Kannada', 'Kannada'),
    ]
    
    LEVEL_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    thumbnail_url = models.URLField(max_length=500, blank=True, null=True)
    category = models.CharField(max_length=100, default="Web Design")
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='Tamil')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=5.0)
    review_count = models.IntegerField(default=1000)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='Beginner')
    
    duration_hours = models.IntegerField(default=2)
    duration_minutes = models.IntegerField(default=0)
    total_lessons = models.IntegerField(default=10)
    total_quizzes = models.IntegerField(default=10)
    
    price = models.DecimalField(max_digits=10, decimal_places=2, default=399.00)
    author_name = models.CharField(max_length=100, default="Kevin Marks")
    author_avatar_url = models.URLField(max_length=500, blank=True, null=True)
    
    short_description = models.TextField(blank=True)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    expiry_duration_days = models.PositiveIntegerField(default=365, help_text="Duration in days for course access after enrollment")
    
    # Security Settings
    prevent_screenshots = models.BooleanField(default=True, help_text="Attempt to block screenshots and screen recording")
    restrict_downloads = models.BooleanField(default=True, help_text="Disable right-click and common download methods")

    class Meta:
        verbose_name_plural = "Courses"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_duration_display(self):
        """Returns formatted duration string."""
        if self.duration_hours and self.duration_minutes:
            return f"{self.duration_hours}h {self.duration_minutes}m"
        elif self.duration_hours:
            return f"{self.duration_hours}h"
        elif self.duration_minutes:
            return f"{self.duration_minutes}m"
        return "N/A"


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    section_name = models.CharField(max_length=255, default="Introduction")
    title = models.CharField(max_length=255)
    slug = models.SlugField(default="lesson-slug")
    video_file = models.FileField(upload_to='protected_videos/', blank=True, null=True, help_text="Upload video for secure streaming")
    video_url = models.URLField(max_length=500, blank=True, null=True, help_text="Fallback stream source URI")
    thumbnail = models.ImageField(upload_to='lesson_thumbnails/', blank=True, null=True)
    is_preview = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    is_locked = models.BooleanField(default=False, help_text="Whether this lesson is locked until previous lessons are completed")
    
    # Lesson Content Types
    lesson_file = models.FileField(upload_to='lesson_files/', blank=True, null=True, help_text="Optional downloadable file for this lesson")
    question_text = models.TextField(blank=True, null=True, help_text="If present, student must answer this to complete the lesson")
    correct_answer = models.CharField(max_length=255, blank=True, null=True, help_text="Required answer if question_text is provided")
    
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['order']
        verbose_name_plural = "Lessons"

    def __str__(self):
        return f"[{self.course.title}] {self.section_name} - {self.title}"


# ==========================================
# 3. ACCESS CONTROL MATRIX
# ==========================================
class CourseAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlocked_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    enrollment_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
        verbose_name_plural = "Course Access Controls"
        ordering = ['-unlocked_at']

    def __str__(self):
        return f"{self.user.username} has access to {self.course.title}"


# ==========================================
# 4. ORDER MANAGEMENT & BILLING RECORDS
# ==========================================
class Order(models.Model):
    PAYMENT_METHODS = [
        ('Razorpay Gateway', 'Razorpay Gateway'),
        ('UPI', 'UPI'),
        ('Credit/Debit Card', 'Credit/Debit Card'),
    ]
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    order_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=100, default="India")
    state_union_territory = models.CharField(max_length=100, blank=True, null=True)
    gst_number = models.CharField(verbose_name="GSTIN (Optional)", max_length=15, blank=True, null=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default='Razorpay Gateway')
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Orders"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = f"#{Order.objects.count() + 2643}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_id} - {self.user.username} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Order Items"
        ordering = ['-created_at']

    def __str__(self):
        return f"Item: {self.course.title if self.course else 'Deleted Course'} for Order {self.order.order_id}"


# ==========================================
# 5. CREDENTIALS & CERTIFICATION
# ==========================================
class Certificate(models.Model):
    certificate_number = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    issue_date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Certificates"
        ordering = ['-issue_date']

    def save(self, *args, **kwargs):
        if not self.certificate_number:
            self.certificate_number = str(uuid.uuid4().int)[:6]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Cert {self.certificate_number} - {self.user.username} - {self.course.title}"


# ==========================================
# 6. OTP SESSION MANAGEMENT
# ==========================================
class OTPSession(models.Model):
    """
    Manages OTP verification sessions for secure phone-based authentication.
    """
    phone_number = models.CharField(max_length=20, unique=True)
    otp_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name_plural = "OTP Sessions"
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP Session for {self.phone_number}"

    def is_expired(self):
        """Check if OTP session has expired."""
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def is_valid_attempt(self):
        """Check if OTP session is still valid for attempts."""
        return not self.is_expired() and self.attempts < 3


# ==========================================
# 7. AUDIT & LOGGING
# ==========================================
class LoginHistory(models.Model):
    """
    Tracks user login events for security and analytics.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    login_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Login History"
        ordering = ['-login_at']

    def __str__(self):
        return f"{self.user.username} logged in at {self.login_at}"

# ==========================================
# 8. MARKETING & SOCIAL PROOF
# ==========================================
class Testimonial(models.Model):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, help_text="e.g., Student, Professional, Trader")
    content = models.TextField()
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Testimonials"
        ordering = ['-created_at']

    def __str__(self):
        return f"Testimonial by {self.name}"
