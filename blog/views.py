from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from .models import Post, Comment, Notification, Genre
from .forms import PostForm, CommentForm, UserRegisterForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from .ai_toxicity import toxicity_classifier

# --- Class-Based Views for Posts ---

class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    ordering = ['-created_at']
    paginate_by = 5
     
    def get_context_data(self, **kwargs):
        # First, get the base context from the original method
        context = super().get_context_data(**kwargs)
        
        # Now, add all the extra data for the new design
        
        # Get the single most recent post for the "hero" section
        context['featured_post'] = Post.objects.order_by('-created_at').first()
        
        # --- Sidebar Data ---
        # Get 5 most popular posts (ordered by number of comments)
        context['popular_posts'] = Post.objects.annotate(
            comment_count=Count('comments')
        ).order_by('-comment_count')[:5]
        
        # Get 5 latest posts
        context['latest_posts'] = Post.objects.order_by('-created_at')[:5]

        # Get 5 most recent approved comments
        context['recent_comments'] = Comment.objects.filter(status='approved').order_by('-created_at')[:5]
        
        # Get all Genres to display in a list
        # Note: A better way for the navbar is a context processor (see next step)
        context['all_genres'] = Genre.objects.all()

        return context
    

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()

        # --- THIS IS THE CORRECTED LOGIC ---
        # Get the current user
        user = self.request.user
        post = self.get_object()

        if user.is_authenticated:
            # If the user is logged in, show them:
            # 1. All 'approved' comments.
            # 2. THEIR OWN comments, regardless of status (so they can see their pending ones).
            visible_comments = post.comments.filter(
                Q(status='approved') | Q(author=user)
            ).distinct().order_by('created_at')
        else:
            # If the user is not logged in, ONLY show 'approved' comments.
            visible_comments = post.comments.filter(status='approved').order_by('created_at')

        context['comments'] = visible_comments
        # ------------------------------------
        
        return context

class PostCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    permission_required = 'blog.add_post'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        return self.request.user == self.get_object().author

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/post_confirm_delete.html'
    success_url = reverse_lazy('post_list')

    def test_func(self):
        return self.request.user == self.get_object().author

# --- Function-Based Views ---

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

def search_results(request):
    query = request.GET.get('q')
    posts = Post.objects.filter(Q(title__icontains=query) | Q(content__icontains=query)).distinct().order_by('-created_at') if query else Post.objects.none()
    return render(request, 'blog/search_results.html', {'posts': posts, 'query': query})

def profile_page(request, username):
    profile_user = get_object_or_404(User, username=username)
    context = {
        'profile_user': profile_user,
        'posts': Post.objects.filter(author=profile_user).order_by('-created_at'),
        'comments': Comment.objects.filter(author=profile_user, status='approved').order_by('-created_at'),
    }
    return render(request, 'blog/profile_page.html', context)

@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            if request.POST.get('parent_id'):
                try:
                    comment.parent = Comment.objects.get(id=request.POST.get('parent_id'))
                except Comment.DoesNotExist:
                    comment.parent = None
            
            is_toxic, label = toxicity_classifier.predict(comment.text)
            if is_toxic:
                comment.status = 'pending_review'
                comment.toxicity_label = label
                comment.save()
                messages.warning(request, f"Your comment was flagged as '{label}' and is now pending review.")
                Notification.objects.create(user=request.user, message=f"Your comment on '{post.title}' is pending review due to: {label}.", comment=comment)
            else:
                comment.status = 'approved'
                comment.toxicity_label = None
                comment.save()
                messages.success(request, 'Your comment has been posted successfully!')
            return redirect('post_detail', pk=post.pk)
        else:
            context = {'post': post, 'comments': post.comments.order_by('created_at'), 'form': form}
            messages.error(request, 'There was an error with your submission.')
            return render(request, 'blog/post_detail.html', context)
    return redirect('post_detail', pk=post.pk)

@login_required
def report_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.status = 'reported'
    comment.save()
    messages.success(request, 'Thank you for your report. An admin will review this comment.')
    return redirect('post_detail', pk=comment.post.pk)

@login_required
def dashboard(request):
    user = request.user
    all_comments = Comment.objects.filter(author=user).order_by('-created_at')
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    notifications.filter(read=False).update(read=True)

    author_stats = {}
    is_author = user.groups.filter(name='Authors').exists()

    if is_author:
        user_posts = Post.objects.filter(author=user)
        first_post = user_posts.order_by('created_at').first()
        author_stats = {
            'total_posts': user_posts.count(),
            'total_comments_received': Comment.objects.filter(post__in=user_posts).count(),
            'time_as_author': timezone.now() - first_post.created_at if first_post else None,
        }

    context = {
        'all_comments': all_comments,
        'action_required_comments': all_comments.filter(status='pending_review'),
        'notifications': notifications,
        'author_stats': author_stats,
        'is_author': is_author,
    }
    return render(request, 'blog/dashboard.html', context)

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('post_list')
    
    moderation_statuses = Q(status='pending_review') | Q(status='reported')
    context = {
        'stats': {
            'total_posts': Post.objects.count(),
            'total_comments': Comment.objects.count(),
            'total_users': User.objects.count(),
            'comments_awaiting_approval': Comment.objects.filter(moderation_statuses).count(),
        },
        'moderation_queue': Comment.objects.filter(moderation_statuses).order_by('-created_at')[:5],
        'recent_posts': Post.objects.order_by('-created_at')[:5],
        'recent_comments': Comment.objects.filter(status='approved').order_by('-created_at')[:5],
    }
    return render(request, 'blog/admin_dashboard.html', context)

@login_required
def admin_comments(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('post_list')

    comments_to_moderate = Comment.objects.filter(Q(status='pending_review') | Q(status='reported')).order_by('-created_at')
    paginator = Paginator(comments_to_moderate, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog/admin_comments.html', {'comments': page_obj})

@login_required
def approve_comment(request, pk):
    if not request.user.is_superuser:
        return redirect('post_list')
    comment = get_object_or_404(Comment, pk=pk)
    comment.status = 'approved'
    comment.save()
    Notification.objects.create(user=comment.author, message=f"Your comment on '{comment.post.title}' has been approved by an admin.", comment=comment)
    messages.success(request, 'Comment approved successfully.')
    return redirect('admin_comments')

@login_required
def delete_comment(request, pk):
    if not request.user.is_superuser:
        return redirect('post_list')
    comment = get_object_or_404(Comment, pk=pk)
    comment.delete()
    messages.success(request, 'Comment deleted successfully.')
    return redirect('admin_comments')

@login_required
def edit_my_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if request.user != comment.author:
        messages.error(request, "You are not authorized to edit this comment.")
        return redirect('post_detail', pk=comment.post.pk)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            edited_comment = form.save(commit=False)
            is_toxic, label = toxicity_classifier.predict(edited_comment.text)
            if is_toxic:
                edited_comment.status = 'pending_review'
                edited_comment.toxicity_label = label
                messages.warning(request, f"Your edited comment was still flagged as '{label}' and requires review.")
            else:
                edited_comment.status = 'approved'
                edited_comment.toxicity_label = None
                messages.success(request, "Your comment has been updated and approved!")
            edited_comment.is_edited = True
            edited_comment.save()
            return redirect('dashboard')
    else:
        form = CommentForm(instance=comment)
    return render(request, 'blog/edit_comment.html', {'form': form, 'comment': comment})

@login_required
def delete_my_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post_pk = comment.post.pk
    if request.user == comment.author or request.user.is_superuser:
        comment.delete()
        messages.success(request, "Your comment has been deleted.")
    else:
        messages.error(request, "You are not authorized to delete this comment.")
    return redirect('post_detail', pk=post_pk)