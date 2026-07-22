from django import forms
from django.contrib.auth.models import User
from .models import Contact
import re


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Password"
        })
    )

    username = forms.CharField(
        label="Username",
        max_length=100,
        help_text="Use only letters, numbers and underscore (_). No spaces.",
        widget=forms.TextInput(attrs={
            "placeholder": "Username"
        })
    )

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    # Username validation
    def clean_username(self):

        username = self.cleaned_data["username"].strip()

        if " " in username:
            raise forms.ValidationError(
                "Username cannot contain spaces."
            )

        if not re.match(r'^[A-Za-z0-9_]+$', username):
            raise forms.ValidationError(
                "Only letters, numbers and underscore (_) are allowed."
            )

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "This username is already taken."
            )

        return username

    # Email validation
    def clean_email(self):

        email = self.cleaned_data["email"].lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "This email is already registered."
            )

        return email
class ContactForm(forms.ModelForm):

    class Meta:

        model = Contact

        fields = [
            "username",
            "email",
            "message"
        ]


        widgets = {

            "username": forms.TextInput(
                attrs={
                    "placeholder":"Name"
                }
            ),


            "email": forms.EmailInput(
                attrs={
                    "placeholder":"your@email.com"
                }
            ),


            "message": forms.Textarea(
                attrs={
                    "placeholder":"Your message",
                    "rows":5
                }
            )

        }