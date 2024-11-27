from django import forms
from .models import *
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(label='', widget=forms.TextInput(attrs={
        'placeholder': 'First Name',
    }))
    last_name = forms.CharField(label='', widget=forms.TextInput(attrs={
        'placeholder': 'Last Name',
    }))
    username = forms.CharField(label='', widget=forms.TextInput(attrs={
        'placeholder': 'User Name',
    }), required=False)
    email = forms.EmailField(label='', widget=forms.EmailInput(attrs={
        'placeholder': 'Email',
    }))
    phone = forms.CharField(label='', widget=forms.TextInput(attrs={
        'placeholder': 'Phone Number',
    }))
    password1 = forms.CharField(label='', widget=forms.PasswordInput(attrs={
        'placeholder': 'Enter Password',
    }))
    password2 = forms.CharField(label='', widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirm Password',
    }))
    
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'phone', 'password1', 'password2', 'username']



class UserAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='',widget=forms.TextInput(attrs={
        'placeholder':'Email or Username',
    }))
    password = forms.CharField(label='',widget=forms.PasswordInput(attrs={
        'placeholder':'Password',
    }))

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = Customer.objects.get(Q(email=username) | Q(username=username))
        except Customer.DoesNotExist:
            raise forms.ValidationError('No user found with this email or username')
        
        return user.email 

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
    street = forms.CharField(label='',widget=forms.TextInput(attrs={
        'placeholder':'Street Name, Building , House No.',
    }))
    city = forms.CharField(label='',widget=forms.TextInput(attrs={
        'placeholder':'Barangay, City, Province, Region',
    }))
    postal = forms.CharField(label='',widget=forms.TextInput(attrs={
        'placeholder':'Postal Code',
    }))

    class Meta:
        model = Address
        fields = ['street', 'city', 'postal']

class ProductSizeForm(forms.Form):
    size = forms.ModelChoiceField(
        queryset=None,
        label="Choose Size",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        if product:
            self.fields['size'].queryset = product.sizes.filter(stock__gt=0)