from django import forms
from django.contrib.auth.models import User
from .models import Contact

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    username =forms.CharField(label='First Name',
    help_text='do not use special characters,Emojis, or do no leave spaces',
            max_length=100, 
            widget=forms.TextInput
            (attrs={'placeholder': 'First Name'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['username', 'email', 'message']

        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Name'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'your@email.com'
            }),
            'message': forms.Textarea(attrs={
                'placeholder': 'Your message',
                'rows': 5
            }),
        }
