from django import forms
from django.contrib.auth.models import User
from .models import Contact

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    avatar = forms.ChoiceField(choices=[(f"avatar{i}.png", f"Avatar {i}") for i in range(1, 71)])

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