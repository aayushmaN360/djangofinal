from django import forms
from .models import Post, Comment, Genre, Profile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class PostForm(forms.ModelForm):
    genre = forms.ModelChoiceField(
        queryset=Genre.objects.all(),
        empty_label="Select a Genre",
        required=True
    )

    class Meta:
        model = Post
        fields = ['title', 'genre', 'content', 'photo']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 7,
                'cols': 67,
                'placeholder': 'Join the discussion...'
            }),
        }

    def clean_text(self):
        text = self.cleaned_data.get('text', '')
        word_limit = 100
        word_count = len(text.split())
        if word_count > word_limit:
            raise forms.ValidationError(
                f"Please keep your comment under {word_limit} words. "
                f"You have used {word_count} words."
            )
        return text

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': "What's on your mind?"})
    )

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

# ✅ Updated version with uniqueness check
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('instance', None)
        self.user = kwargs.pop('user', self.user)
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        existing_user = User.objects.filter(username=username).exclude(pk=self.user.pk).first()
        if existing_user:
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        existing_user = User.objects.filter(email=email).exclude(pk=self.user.pk).first()
        if existing_user:
            raise forms.ValidationError('This email is already taken.')
        return email

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'bio']
