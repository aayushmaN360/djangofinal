# File: toxicity_blog/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# This is the correct order for the URL patterns.
# Your app's URLs are checked before the Django admin URLs.
urlpatterns = [
     # ✅ Root-level blog URLs
     path('', include('blog.urls')),

    # 2. The admin path comes AFTER. Django will only check this if no match was found above.
    path('admin/', admin.site.urls),

    # 3. The accounts path is also specific.
    path('accounts/', include('django.contrib.auth.urls')),
]

# This part is for serving user-uploaded media files (like post photos) during development.
# It should be added at the end.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
