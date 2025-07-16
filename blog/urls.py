from django.urls import path
from . import views
from .views import (
    PostListView, 
    PostDetailView, 
    PostCreateView, 
    PostUpdateView, 
    PostDeleteView
)

urlpatterns = [
    path('', PostListView.as_view(), name='post_list'),
    path('post/<int:pk>/', PostDetailView.as_view(), name='post_detail'),
    path('post/new/', PostCreateView.as_view(), name='post_create'),
    path('post/<int:pk>/update/', PostUpdateView.as_view(), name='post_update'),
    path('post/<int:pk>/delete/', PostDeleteView.as_view(), name='post_delete'),
    
    path('register/', views.register, name='register'),
    path('post/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin/comments/', views.admin_comments, name='admin_comments'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('comment/<int:pk>/approve/', views.approve_comment, name='approve_comment'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
    path('comment/<int:pk>/edit/', views.edit_my_comment, name='edit_my_comment'),
    path('comment/<int:pk>/delete_own/', views.delete_my_comment, name='delete_my_comment'),
]
