from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from ckeditor.fields import RichTextField 

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Enter a post genre (e.g. Technology, Lifestyle)")

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=200)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True)
    content = RichTextField()
    photo = models.ImageField(upload_to='post_photos/', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'pk': self.pk})
    
    def approved_comments(self):
        return self.comments.filter(approved=True)

# =============================================================================
# CHANGES ARE IN THIS MODEL
# =============================================================================
class Comment(models.Model):
    # Define the choices for the new status field
    STATUS_CHOICES = (
        ('approved', 'Approved'),
        ('pending_review', 'Pending Review'),
        ('reported', 'Reported'),  # For toxic comments
        ('rejected', 'Rejected'),             # Optional status for admins
    )

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # The new, single field for status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    
    # We still keep these for context
    toxicity_label = models.CharField(max_length=50, null=True, blank=True)
    is_edited = models.BooleanField(default=False)

    def __str__(self):
        return f"Comment by {self.author} on {self.post.title}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Notification for {self.user}: {self.message}"