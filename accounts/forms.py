from django import forms
from django.contrib.auth.models import User

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
class ContactForm(forms.Form):
        username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Name'}))
        email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'your@email.com'}))
        message = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Your message', 'rows': 5}))
          
    