from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control', # You can remove this if you aren't using Bootstrap
        'placeholder': 'Enter your email address'
    }))

    class Meta:
        model = User
        # We only ask for email and passwords. Username is hidden.
        fields = ("email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        # Automatically set the username to be the email address
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user