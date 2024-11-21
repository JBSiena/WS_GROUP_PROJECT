from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(label='',widget=forms.TextInput(attrs={
        'placeholder':'First Name',
    }))
    last_name = forms.CharField(label='',widget=forms.TextInput(attrs={
        'placeholder':'Last Name',
    }))
    email = forms.EmailField(label='',widget=forms.EmailInput(attrs={
        'placeholder':'Email',
    }))
    phone = forms.CharField(label='',widget=forms.TextInput(attrs={
        'placeholder':'Phone Number',
    }))
    password1 = forms.CharField(label='',widget=forms.PasswordInput(attrs={
        'placeholder':'Enter Password',
    }))
    password2 = forms.CharField(label='',widget=forms.PasswordInput(attrs={
        'placeholder':'Confirm Password',
    }))
    
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'phone', 'password1', 'password2']
        
class UserAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder':'Email',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder':'Enter Password',
    }))
    
class EditProfileForm(forms.ModelForm):
    first_name = forms.CharField(label='First Name',widget=forms.TextInput(attrs={
        'placeholder':'First Name',
    }))
    last_name = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':'Last Name',
    }))
    phone = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':'Phone Number',
    }))

    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'phone', 'image']


class AddressForm(forms.ModelForm):
    street = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':'Street',
    }))
    city = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':'Last Name',
    }))
    purok = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':'Phone Number',
    }))
    landmark = forms.CharField(widget=forms.Textarea(attrs={
        'placeholder':'Landmark',
    }))

    class Meta:
        model = Address
        fields = ['street', 'city', 'purok', 'landmark']