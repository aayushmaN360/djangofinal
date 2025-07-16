# File: toxicity_blog/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# This is the correct order for the URL patterns.
# Your app's URLs are checked before the Django admin URLs.
urlpatterns = [
    
    # 1. This includes all URLs from your 'blog' app (like admin/comments/).
    #    It will be checked first.
    path('', include('blog.urls')),

    # 2. This includes the default Django admin site (for managing models).
    #    It will be checked second.
    path('admin/', admin.site.urls),

    # 3. This includes all the built-in authentication URLs (login, logout, etc.).
    path('accounts/', include('django.contrib.auth.urls')),

]

# This part is for serving user-uploaded media files (like post photos) during development.
# It should be added at the end.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
