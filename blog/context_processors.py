from .models import Notification, Genre

# Rename this function to match what settings.py is looking for
def extras_context(request):
    """
    This context processor makes extra data available to ALL templates.
    """
    context = {
        'unread_notifications_count': 0,
        'all_genres': Genre.objects.all()
    }

    if request.user.is_authenticated:
        context['unread_notifications_count'] = Notification.objects.filter(user=request.user, read=False).count()
    
    return context