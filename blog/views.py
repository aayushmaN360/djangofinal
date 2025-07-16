from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from .models import Post, Comment, Notification
from .forms import PostForm, CommentForm, UserRegisterForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count
from .ai_toxicity import toxicity_classifier

# --- Class-Based Views for Posts ---

class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    ordering = ['-created_at']
    paginate_by = 5

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        return context

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    
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
        post = self.get_object()
        return self.request.user == post.author

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/post_confirm_delete.html'
    success_url = reverse_lazy('post_list')
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

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

@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            
            # This part uses the classifier
            is_toxic, label = toxicity_classifier.predict(comment.text)
            
            if is_toxic:
                # --- THIS IS THE TOXIC PATH ---
                comment.toxic = True
                comment.approved = False
                comment.toxicity_label = label  # Store the specific label
                comment.save()
                
                Notification.objects.create(
                    user=request.user,
                    message=f"Your comment on '{post.title}' was flagged as '{label}'. Please edit it.",
                    comment=comment
                )
                messages.warning(request, f"Your comment was flagged as '{label}' and has been blocked. You can edit or delete it below.")
            else:
                # --- THIS IS THE NON-TOXIC PATH ---
                comment.toxic = False
                comment.approved = True
                comment.toxicity_label = 'clean' # Or leave it blank
                comment.save()
                messages.success(request, 'Your comment has been posted!')
            
            return redirect('post_detail', pk=post.pk)
    return redirect('post_detail', pk=post.pk)
# --- USER DASHBOARD ---
@login_required
def dashboard(request):
    # Get all comments by the user
    all_comments = Comment.objects.filter(author=request.user).order_by('-created_at')
    
    # --- THIS IS THE FIX ---
    # Instead of filtering by 'toxic' and 'approved', we filter by the new 'status' field.
    action_required_comments = all_comments.filter(status='pending_review')
    
    # Get and mark notifications as read
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifications.filter(read=False).update(read=True)
    
    context = {
        'all_comments': all_comments,
        'action_required_comments': action_required_comments,
        'notifications': notifications,
    }
    return render(request, 'blog/dashboard.html', context)

# --- ADMIN DASHBOARD ---
@login_required
def admin_dashboard(request):
    # Security Check: Only superusers can access this page.
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('post_list')
    
    # --- Data Gathering ---

    # 1. "At a Glance" Statistics
    stats = {
        'total_posts': Post.objects.count(),
        'total_comments': Comment.objects.count(),
        'total_users': User.objects.count(),
        # Get count of comments that need review.
        'comments_awaiting_approval': Comment.objects.filter(status='pending_review').count()
    }
    
    # 2. Moderation Queue: Get the 5 most recent comments awaiting review.
    moderation_queue = Comment.objects.filter(status='pending_review').order_by('-created_at')[:5]
    
    # 3. Recent Activity Feeds
    recent_posts = Post.objects.order_by('-created_at')[:5]
    recent_comments = Comment.objects.filter(status='approved').order_by('-created_at')[:5]

    # --- Context ---
    # Package all the data to send to the template.
    context = {
        'stats': stats,
        'moderation_queue': moderation_queue,
        'recent_posts': recent_posts,
        'recent_comments': recent_comments,
    }
    
    # Render the page using the template we will create next.
    return render(request, 'blog/admin_dashboard.html', context)

# --- Admin and User Comment Management ---

@login_required
def admin_comments(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('post_list')
    
    toxic_comments = Comment.objects.filter(toxic=True, approved=False).order_by('-created_at')
    paginator = Paginator(toxic_comments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'comments': page_obj}
    return render(request, 'blog/admin_comments.html', context)

@login_required
def approve_comment(request, pk):
    if not request.user.is_superuser:
        return redirect('post_list')
    
    comment = get_object_or_404(Comment, pk=pk)
    comment.approved = True
    comment.toxic = False
    comment.save()
    
    Notification.objects.create(
        user=comment.author,
        message=f"Your comment on '{comment.post.title}' has been approved by an admin.",
        comment=comment
    )
    
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
            edited_comment.is_edited = True
            
            is_toxic, label = toxicity_classifier.predict(edited_comment.text)
            
            if is_toxic:
                edited_comment.toxic = True
                edited_comment.approved = False
                edited_comment.toxicity_label = label
                messages.warning(request, f"Your edited comment was still flagged as '{label}'. Please revise it.")
            else:
                edited_comment.toxic = False
                edited_comment.approved = True
                edited_comment.toxicity_label = None
                messages.success(request, "Your comment has been updated and approved!")

            edited_comment.save()
            return redirect('post_detail', pk=comment.post.pk)
    else:
        form = CommentForm(instance=comment)
        
    return render(request, 'blog/edit_comment.html', {'form': form, 'comment': comment})

@login_required
def delete_my_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    
    if request.user != comment.author and not request.user.is_superuser:
        messages.error(request, "You are not authorized to delete this comment.")
        return redirect('post_detail', pk=comment.post.pk)
    
    post_pk = comment.post.pk
    comment.delete()
    messages.success(request, "Your comment has been deleted.")
    return redirect('post_detail', pk=post_pk)