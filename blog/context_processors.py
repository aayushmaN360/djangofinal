from .models import Notification, Genre ,SiteSettings

# Rename this function to match what settings.py is looking for
def extras_context(request):
    """
    This context processor makes extra data available to ALL templates.
    """
    context = {
        'unread_notifications_count': 0,
        'all_genres': Genre.objects.all(),
        'site_settings': SiteSettings.objects.first() 
    }

    if request.user.is_authenticated:
        context['unread_notifications_count'] = Notification.objects.filter(user=request.user, read=False).count()
    
    return context