# blog/urls.py
# This is the corrected and final version.

from django.urls import path
from . import views

urlpatterns = [
    # --- Main Public Pages ---
    # The root URL '' correctly points to the PostListView, making it the homepage.
    path('', views.PostListView.as_view(), name='post_list'),
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    
    # --- Static Pages (Public) ---
    path('about/', views.about, name='about'),
    path('privacy/', views.privacy, name='privacy'),
    path('contacts/', views.contacts, name='contacts'),
    
    # --- Search and Profile (Public) ---
    path('search/', views.search_results, name='search_results'),
    path('profile/<str:username>/', views.profile_page, name='profile_page'),
  

    

    # --- User Authentication ---
    path('register/', views.register, name='register'),
    # Note: 'login' and 'logout' are handled by your project's auth URLs

    # --- PROTECTED User and Admin Views (Login Required) ---
    path('dashboard/', views.dashboard, name='dashboard'), # Dashboard has its own URL.
    path('post/new/', views.PostCreateView.as_view(), name='post_create'),
    path('post/<int:pk>/update/', views.PostUpdateView.as_view(), name='post_update'),
    path('post/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    
    # --- PROTECTED Comment Actions ---
    path('post/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:pk>/edit/', views.edit_my_comment, name='edit_my_comment'),
    path('comment/<int:pk>/delete_own/', views.delete_my_comment, name='delete_my_comment'),
    path('comment/<int:pk>/report/', views.report_comment, name='report_comment'),

    # --- PROTECTED Admin Views ---
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/comments/', views.admin_comments, name='admin_comments'),
    path('admin/comment/<int:pk>/approve/', views.approve_comment, name='approve_comment'),
    path('admin/comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
]