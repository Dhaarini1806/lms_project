import os
import django
from django.utils.text import slugify

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms_project.settings')
django.setup()

from core.models import Course, Lesson

def seed_huge_course():
    # 1. Create the Course
    course_title = "The Ultimate Trading Mastery: Zero to Pro"
    course_slug = slugify(course_title)
    
    course, created = Course.objects.update_or_create(
        slug=course_slug,
        defaults={
            'title': course_title,
            'thumbnail_url': 'https://images.unsplash.com/photo-1611974714658-058f40da23bb?auto=format&fit=crop&w=800&q=80',
            'category': 'Trading Strategy',
            'language': 'English',
            'rating': 4.9,
            'review_count': 12500,
            'level': 'Advanced',
            'duration_hours': 45,
            'duration_minutes': 30,
            'total_lessons': 12,
            'total_quizzes': 5,
            'price': 1999.00,
            'author_name': 'Alexander Sterling',
            'author_avatar_url': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=100&q=80',
            'short_description': 'Master the markets with our most comprehensive curriculum ever. From basics to institutional algorithms.',
            'description': 'This is the ultimate guide to trading. You will learn everything from market psychology to complex technical analysis and risk management.',
            'is_published': True,
        }
    )
    
    if created:
        print(f"✓ Created course: {course.title}")
    else:
        print(f"✓ Updated course: {course.title}")

    # 2. Create Lessons (Some Preview, Most Locked)
    lessons_data = [
        # Module 1: Foundations (Preview)
        {"title": "Introduction to Market Dynamics", "preview": True, "order": 1},
        {"title": "Psychology of a Winning Trader", "preview": True, "order": 2},
        
        # Module 2: Technical Analysis (Locked)
        {"title": "Advanced Candlestick Patterns", "preview": False, "order": 3},
        {"title": "Mastering Support & Resistance", "preview": False, "order": 4},
        {"title": "Fibonacci Retracement Secrets", "preview": False, "order": 5},
        
        # Module 3: Strategy (Locked)
        {"title": "The Institutional Flow Strategy", "preview": False, "order": 6},
        {"title": "Risk Management & Position Sizing", "preview": False, "order": 7},
        {"title": "Trading with the Trend", "preview": False, "order": 8},
        
        # Module 4: Live Execution (Locked)
        {"title": "Live Session: Identifying Entry Points", "preview": False, "order": 9},
        {"title": "Advanced Stop Loss Techniques", "preview": False, "order": 10},
        {"title": "Building Your Personal Trading Plan", "preview": False, "order": 11},
        {"title": "Final Assessment & Graduation", "preview": False, "order": 12},
    ]

    for data in lessons_data:
        lesson, l_created = Lesson.objects.update_or_create(
            course=course,
            title=data['title'],
            defaults={
                'slug': slugify(data['title']),
                'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ', # Placeholder
                'is_preview': data['preview'],
                'order': data['order'],
            }
        )
        status = "Created" if l_created else "Updated"
        print(f"  - {status} lesson: {lesson.title} (Preview: {lesson.is_preview})")

if __name__ == "__main__":
    seed_huge_course()
