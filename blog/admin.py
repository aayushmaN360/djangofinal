from django.contrib import admin
from django.utils.html import format_html # <-- Import this
from .models import Post, Comment, Notification, Genre


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author','genre', 'created_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at', 'author','genre')

# =============================================================================
# THIS IS THE CORRECTED CLASS
# =============================================================================
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    # Use the new display_status function in the list display
    list_display = ('post', 'author', 'created_at', 'display_status', 'toxicity_label')
    list_filter = ('status', 'created_at', 'post')
    search_fields = ('text', 'author__username', 'post__title')
    
    # Define the actions
    actions = ['approve_comments', 'delete_reported_comments']

    # 1. NEW FUNCTION to add color to the status column
    def display_status(self, obj):
        if obj.status == 'approved':
            color = 'green'
        elif obj.status == 'pending_review':
            color = 'orange'
        elif obj.status == 'reported':
            color = 'red'
        else:
            color = 'black'
        # get_status_display() shows the user-friendly name (e.g., "Pending Review")
        return format_html(f'<b style="color: {color};">{obj.get_status_display()}</b>')
    
    display_status.short_description = 'Status'
    display_status.admin_order_field = 'status'

    # 2. RENAMED ACTION for clarity
    def approve_comments(self, request, queryset):
        # Update the status to 'approved'
        queryset.update(status='approved')
    approve_comments.short_description = "Mark selected comments as Approved"

    # 3. IMPROVED ACTION to delete instead of just marking as rejected
    def delete_reported_comments(self, request, queryset):
        # This is more decisive for bad comments
        queryset.delete()
    delete_reported_comments.short_description = "Delete selected comments"

# =============================================================================
# NO CHANGES NEEDED BELOW
# =============================================================================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at', 'read')
    list_filter = ('read', 'created_at')