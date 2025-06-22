from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(max_length=255, required=True, help_text="Required. Enter a valid email address.",
                             widget=forms.EmailInput(attrs={'class':'form-control', 'placeholder': 'Email Address'}))
    
    class Meta:
        model = User
        fields = ('username', 'email')

        def save(self, commit=True):
            user = super().save(commit=False)
            user.email = self.cleaned_data['email']
            if commit:
                user.save()
            return user
        

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder': 'Password'}))
