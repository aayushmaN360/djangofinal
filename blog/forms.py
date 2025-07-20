from django import forms
from .models import Post, Comment ,Genre
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class PostForm(forms.ModelForm):
    genre = forms.ModelChoiceField(
        queryset=Genre.objects.all(),
        empty_label="Select a Genre",
        required=True # Added a comma here if you add more options later
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
                'rows': 7,  # You can change this number! 3 is a good starting point.
                'cols':100,
                'placeholder': 'Join the discussion...' # A nice extra touch
            }),
        }
    def clean_text(self):
        # First, get the submitted text from the form's cleaned data
        text = self.cleaned_data.get('text', '')

        # Define your word limit
        word_limit = 100

        # Split the text by spaces to count the words
        word_count = len(text.split())

        # Check if the word count exceeds the limit
        if word_count > word_limit:
            # If it does, raise a ValidationError. Django will automatically
            # attach this error message to the 'text' field in the form.
            raise forms.ValidationError(
                f"Please keep your comment under {word_limit} words. "
                f"You have used {word_count} words."
            )
        
        # If the validation passes, always return the cleaned data
        return text

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        
        # --- THIS IS THE MAGIC PART ---
        # This loop adds the 'form-control' class to make the fields look good
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'   