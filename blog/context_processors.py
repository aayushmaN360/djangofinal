from .models import Notification

def notifications_processor(request):  # <--- The function name is "notifications_processor"
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, read=False).count()
        return {'unread_notifications_count': unread_count}
    return {}