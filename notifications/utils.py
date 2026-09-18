from .models import Notification


def notify(recipient, title, message, notification_type=Notification.NotificationType.GENERAL, link_url=''):
    """
    Central helper for creating notifications. Any app can call this
    instead of duplicating Notification.objects.create(...) logic.
    """
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        link_url=link_url,
    )