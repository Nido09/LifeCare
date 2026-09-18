from .models import Notification
from django.db import connection

def unread_notifications(request):
    # Check if the notifications table exists first
    table_name = Notification._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = %s
        """, [table_name])
        table_exists = cursor.fetchone()[0] > 0
    
    if not table_exists:
        return {'unread_notification_count': 0, 'recent_notifications': []}
    
    try:
        if request.user.is_authenticated:
            count = Notification.objects.filter(recipient=request.user, is_read=False).count()
            recent = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5]
        else:
            count = 0
            recent = []
        return {'unread_notification_count': count, 'recent_notifications': recent}
    except Exception:
        return {'unread_notification_count': 0, 'recent_notifications': []}