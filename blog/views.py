# blog/views.py

# --- Django and Python Imports ---
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.utils import timezone



# --- Your Application's Imports ---
# CORRECTED: Added 'Profile' to the model imports
from .models import Post, Comment, Notification, Genre, Profile 
# CORRECTED: Combined all form imports into one line for cleanliness
from .forms import PostForm, CommentForm, UserRegisterForm, UserUpdateForm, ProfileUpdateForm 
from .ai_toxicity import toxicity_classifier # Assuming this file exists in your app


# ==============================================================================
# --- PUBLIC-FACING VIEWS (Visible to Everyone) ---
# ==============================================================================

class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    ordering = ['-created_at']
    paginate_by = 5
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_post'] = Post.objects.order_by('-created_at').first()
        context['popular_posts'] = Post.objects.annotate(comment_count=Count('comments')).order_by('-comment_count')[:5]
        context['recent_comments'] = Comment.objects.filter(status='approved').order_by('-created_at')[:5]
        context['all_genres'] = Genre.objects.all()
        return context

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        user = self.request.user
        post = self.get_object()
        if user.is_authenticated:
            context['comments'] = post.comments.filter(Q(status='approved') | Q(author=user)).distinct().order_by('created_at')
        else:
            context['comments'] = post.comments.filter(status='approved').order_by('created_at')
        return context

def search_results(request):
    query = request.GET.get('q')
    posts = Post.objects.filter(Q(title__icontains=query) | Q(content__icontains=query)).distinct().order_by('-created_at') if query else Post.objects.none()
    return render(request, 'blog/search_results.html', {'posts': posts, 'query': query})

def profile_page(request, username):
    profile_user = get_object_or_404(User, username=username)
    Profile.objects.get_or_create(user=profile_user) # This will now work
    context = {
        'profile_user': profile_user,
        'posts': Post.objects.filter(author=profile_user).order_by('-created_at'),
        'comments': Comment.objects.filter(author=profile_user, status='approved').order_by('-created_at'),
    }
    return render(request, 'blog/profile_page.html', context) # You were missing a return here
@login_required
def profile_edit(request):
    Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile_page', username=request.user.username)
        else:
            # Re-render the profile page with error messages in the modal
            messages.error(request, 'Please correct the error(s) below.')
            context = { 'u_form': u_form, 'p_form': p_form }
            return render(request, 'blog/profile.html', context)  # Make sure your modal lives here!
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = { 'u_form': u_form, 'p_form': p_form }
    return render(request, 'blog/profile.html', context)

# ==============================================================================
# --- USER REGISTRATION & PROTECTED VIEWS ---
# ==============================================================================

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})

class PostCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Post; form_class = PostForm; template_name = 'blog/post_form.html'; permission_required = 'blog.add_post'
    def form_valid(self, form): form.instance.author = self.request.user; return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post; form_class = PostForm; template_name = 'blog/post_form.html'
    def test_func(self): return self.request.user == self.get_object().author

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post; template_name = 'blog/post_confirm_delete.html'; success_url = reverse_lazy('post_list')
    def test_func(self): return self.request.user == self.get_object().author

@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False); comment.post = post; comment.author = request.user
            is_toxic, label = toxicity_classifier.predict(comment.text)
            if is_toxic:
                comment.status = 'pending_review'; comment.toxicity_label = label; comment.save()
                messages.warning(request, f"Your comment was flagged as '{label}' and is now pending review.")
                Notification.objects.create(user=request.user, message=f"Your comment on '{post.title}' is pending review due to: {label}.", comment=comment)
            else:
                comment.status = 'approved'; comment.save()
                messages.success(request, 'Your comment has been posted successfully!')
            return redirect('post_detail', pk=post.pk)
    return redirect('post_detail', pk=post.pk)

@login_required
def report_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk); comment.status = 'reported'; comment.save()
    messages.success(request, 'Thank you for your report. An admin will review this comment.')
    return redirect('post_detail', pk=comment.post.pk)
@login_required
def dashboard(request):
    user = request.user

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=user, user=user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the error(s) below.')
    else:
        u_form = UserUpdateForm(instance=user, user=user)
        p_form = ProfileUpdateForm(instance=user.profile)

    all_comments = Comment.objects.filter(author=user).order_by('-created_at')
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    notifications.filter(read=False).update(read=True)

    is_author = user.groups.filter(name='Authors').exists() or user.is_superuser
    user_posts = Post.objects.filter(author=user) if is_author else []

    context = {
        'all_comments': all_comments,
        'action_required_comments': all_comments.filter(status='pending_review'),
        'notifications': notifications,
        'is_author': is_author,
        'u_form': u_form,
        'p_form': p_form,
        'user_posts': user_posts,
        'author_stats': {},
        'existing_usernames': list(User.objects.exclude(pk=user.pk).values_list('username', flat=True)),  # 👈 HERE
    }

    if is_author and user_posts.exists():
        first_post = user_posts.order_by('created_at').first()
        context['author_stats'] = {
            'total_posts': user_posts.count(),
            'total_comments_received': Comment.objects.filter(post__in=user_posts).count(),
            'time_as_author': timezone.now() - first_post.created_at if first_post else None,
        }

    return render(request, 'blog/dashboard.html', context)

@login_required
def admin_dashboard(request):
    # This permission check is crucial
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('post_list')
    
    # Define the statuses that require a moderator's attention
    moderation_statuses = Q(status='pending_review') | Q(status='reported')

    # Gather all the statistics and recent items for the dashboard
    context = {
        'stats': {
            'total_posts': Post.objects.count(),
            'total_comments': Comment.objects.count(),
            'total_users': User.objects.count(),
            'comments_to_moderate_count': Comment.objects.filter(moderation_statuses).count(),
        },
        'moderation_queue': Comment.objects.filter(moderation_statuses).order_by('-created_at')[:5],
        'recent_posts': Post.objects.order_by('-created_at')[:5],
        'recent_approved_comments': Comment.objects.filter(status='approved').order_by('-created_at')[:5],
    }
    return render(request, 'blog/admin_dashboard.html', context)
@login_required
def admin_comments(request):
    if not request.user.is_superuser: messages.error(request, "You do not have permission to access this page."); return redirect('post_list')
    comments_to_moderate = Comment.objects.filter(Q(status='pending_review') | Q(status='reported')).order_by('-created_at')
    paginator = Paginator(comments_to_moderate, 10); page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog/admin_comments.html', {'comments': page_obj})

@login_required
def approve_comment(request, pk):
    if not request.user.is_superuser: return redirect('post_list')
    comment = get_object_or_404(Comment, pk=pk); comment.status = 'approved'; comment.save()
    Notification.objects.create(user=comment.author, message=f"Your comment on '{comment.post.title}' has been approved by an admin.", comment=comment)
    messages.success(request, 'Comment approved successfully.')
    return redirect('admin_comments')

@login_required
def delete_comment(request, pk):
    if not request.user.is_superuser: return redirect('post_list')
    comment = get_object_or_404(Comment, pk=pk); comment.delete()
    messages.success(request, 'Comment deleted successfully.')
    return redirect('admin_comments')

@login_required
def edit_my_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            edited_comment = form.save(commit=False)
            is_toxic, label = toxicity_classifier.predict(edited_comment.text)
            if is_toxic:
                edited_comment.status = 'pending_review'; edited_comment.toxicity_label = label
                messages.warning(request, f"Your edited comment was still flagged as '{label}' and requires review.")
            else:
                edited_comment.status = 'approved'; messages.success(request, "Your comment has been updated and approved!")
            edited_comment.is_edited = True; edited_comment.save()
            return redirect('dashboard')
    else:
        form = CommentForm(instance=comment)
    return render(request, 'blog/edit_comment.html', {'form': form, 'comment': comment})

@login_required
def delete_my_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk); post_pk = comment.post.pk
    if request.user == comment.author or request.user.is_superuser:
        comment.delete(); messages.success(request, "Your comment has been deleted.")
    else:
        messages.error(request, "You are not authorized to delete this comment.")
    return redirect('post_detail', pk=post_pk)

def about(request):
    """Renders the static About page."""
    return render(request, 'blog/about.html')

def contacts(request):
    """Renders the static Contact page."""
    return render(request, 'blog/contacts.html')

def privacy(request):
    """Renders the static Privacy Policy page."""
    return render(request, 'blog/privacy.html')