from django.contrib import admin
from .models import Post, Comment, Notification

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at', 'author')

# =============================================================================
# THIS IS THE CLASS YOU NEED TO MODIFY
# =============================================================================
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    # Use the new 'status' field for display and filtering
    list_display = ('post', 'author', 'created_at', 'status', 'toxicity_label')
    list_filter = ('status', 'created_at', 'post') # Filter by the new status
    
    # We can create a new action to approve comments
    actions = ['approve_comments', 'reject_comments']

    def approve_comments(self, request, queryset):
        # Update the status of the selected comments to 'approved'
        queryset.update(status='approved')
    approve_comments.short_description = "Approve selected comments"

    def reject_comments(self, request, queryset):
        # Update the status to 'rejected'
        queryset.update(status='rejected')
    reject_comments.short_description = "Reject selected comments"

# =============================================================================
# NO CHANGES NEEDED BELOW
# =============================================================================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at', 'read')
    list_filter = ('read', 'created_at')