import os
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms_project.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Profile, Course, Lesson, Order, OrderItem, CourseAccess, Certificate

def create_sample_data():
    print("Creating sample data...")

    # 1. Create Master Admin
    if not User.objects.filter(username='1111111111').exists():
        admin_user = User.objects.create_superuser(
            username='1111111111',
            email='admin@tradersfy.com',
            password='adminpassword123'
        )
        Profile.objects.create(
            user=admin_user,
            full_name='Master Admin',
            phone_number='1111111111',
            user_type='instructor'
        )
        print("Created Master Admin user (1111111111)")

    # 2. Create Sample Courses
    courses_data = [
        {
            'title': 'Complete Stock Market Trading Masterclass',
            'slug': 'stock-market-masterclass',
            'description': 'Learn everything from basics to advanced trading strategies. This comprehensive course covers technical analysis, fundamental analysis, risk management, and trading psychology.',
            'language': 'English',
            'level': 'Beginner',
            'price': Decimal('4999.00'),
            'author_name': 'Kevin Marks',
            'rating': Decimal('4.8'),
            'duration': timedelta(hours=15, minutes=30),
            'is_published': True
        },
        {
            'title': 'Advanced Options Trading Strategies',
            'slug': 'advanced-options-trading',
            'description': 'Master complex options strategies including iron condors, straddles, and spreads. Learn how to profit in any market condition.',
            'language': 'English',
            'level': 'Advanced',
            'price': Decimal('7999.00'),
            'author_name': 'Sarah Jenkins',
            'rating': Decimal('4.9'),
            'duration': timedelta(hours=12, minutes=45),
            'is_published': True
        },
        {
            'title': 'Cryptocurrency Trading for Beginners',
            'slug': 'crypto-trading-beginners',
            'description': 'Start your journey in the world of crypto. Understand blockchain technology, wallets, exchanges, and basic trading strategies.',
            'language': 'Hindi',
            'level': 'Beginner',
            'price': Decimal('2999.00'),
            'author_name': 'Rahul Sharma',
            'rating': Decimal('4.6'),
            'duration': timedelta(hours=8, minutes=15),
            'is_published': True
        }
    ]

    created_courses = []
    for data in courses_data:
        course, created = Course.objects.get_or_create(
            slug=data['slug'],
            defaults=data
        )
        created_courses.append(course)
        if created:
            print(f"Created course: {course.title}")

    # 3. Create Sample Lessons
    if created_courses:
        course1 = created_courses[0]
        lessons_data = [
            {
                'course': course1,
                'title': 'Introduction to Stock Markets',
                'slug': 'intro-stock-markets',
                'description': 'Understanding what stocks are and how the market works.',
                'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'duration': 45,
                'order': 1,
                'resources': 'Download the beginner guide PDF.'
            },
            {
                'course': course1,
                'title': 'Technical Analysis Basics',
                'slug': 'technical-analysis-basics',
                'description': 'Learn to read charts, identify trends, and use basic indicators.',
                'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'duration': 60,
                'order': 2,
                'resources': 'Chart patterns cheat sheet.'
            },
            {
                'course': course1,
                'title': 'Risk Management Strategies',
                'slug': 'risk-management',
                'description': 'How to protect your capital and manage position sizing.',
                'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'duration': 50,
                'order': 3,
                'resources': 'Position sizing calculator excel sheet.'
            }
        ]

        for data in lessons_data:
            lesson, created = Lesson.objects.get_or_create(
                slug=data['slug'],
                defaults=data
            )
            if created:
                print(f"Created lesson: {lesson.title}")

    # 4. Create Sample User and Order
    if not User.objects.filter(username='9876543210').exists():
        student_user = User.objects.create_user(
            username='9876543210',
            email='student@example.com',
            password='studentpassword123'
        )
        Profile.objects.create(
            user=student_user,
            full_name='John Doe',
            phone_number='9876543210',
            user_type='student',
            state='Maharashtra',
            city='Mumbai',
            street_address='123 Trading Street'
        )
        print("Created sample student user (9876543210)")

        # Create Order
        if created_courses:
            course = created_courses[0]
            order = Order.objects.create(
                user=student_user,
                order_id='rzp_mock_id_123456',
                total=course.price * Decimal('1.18'),
                original_price=course.price,
                tax=course.price * Decimal('0.18'),
                status='completed',
                payment_method='razorpay',
                state_union_territory='Maharashtra',
                country='India',
                street_address='123 Trading Street'
            )
            
            OrderItem.objects.create(
                order=order,
                course=course,
                price=course.price
            )

            CourseAccess.objects.create(
                user=student_user,
                course=course
            )

            Certificate.objects.create(
                user=student_user,
                course=course,
                certificate_number='CERT-123456789'
            )
            print("Created sample order, course access, and certificate for student")

    print("Sample data generation complete!")

if __name__ == '__main__':
    create_sample_data()
