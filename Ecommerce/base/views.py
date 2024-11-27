from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import *
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import *

# Home Page - Show products
def home(request):
    categories = Category.objects.all()
    active_products = Product.objects.filter(is_active=True)
    selected_products = random.sample(list(active_products), min(len(active_products), 10))

    return render(request, 'base/home.html', {
        'categories': categories, 
        'products': selected_products,
        })
    
def search_product(request):
    if request.method == 'POST':
        searched = request.POST['searched']
        
        # Search for SCategories
        subcategories = Category.objects.filter(name__icontains=searched)
        
        # Fetch Products associated with the matched Categories
        products = Product.objects.filter(
            Q(name__icontains=searched) |
            Q(category__in=subcategories)
        )
        
        return render(request, 'base/search_product.html', {
            'searched': searched,
            'products': products,
            'subcategories': subcategories,
        })

    return render(request, 'base/search_product.html', {})

# Product Detail
def product_detail(request, pk):
    # Fetch the product based on ID
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        # Handle size selection
        form = ProductSizeForm(request.POST, product=product)
        if form.is_valid():
            selected_size = form.cleaned_data['size']
            # TODO: Add logic to add product and size to the cart
            print(f"Selected size: {selected_size}")
            return redirect('home')  # Redirect after selection
    else:
        form = ProductSizeForm(product=product)

    return render(request, 'base/product_detail.html', {
        'product': product,
        'form': form,
    })


# Edit User Customer
@login_required
def edit_customer(request,pk):
    if request.method == 'POST':
        user = Customer.objects.get(id=pk)
        form = EditProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save() # Save the New User Information
            return redirect('home')
    else:
        user = Customer.objects.get(id=pk)
        form = EditProfileForm(instance=user)
    return render(request, 'base/edit_profile.html', {'form': form})

@login_required
def address(request,pk):
    user_address = Address.objects.filter(user=request.user).first()
    if request.method == 'POST':
        address_form = AddressForm(request.POST)
        if address_form.is_valid():
            # If the user already has an address, update it
            address = address_form.save(commit=False)
            if user_address:
                address.id = user_address.id  # Update the existing address
            address.user = request.user  # Ensure the user field is populated
            address.save()
            return redirect('home')
    else:
        address_form = AddressForm(instance=user_address)

    return render(request, 'base/address.html', {'form': address_form})


# Register view
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        address_form = AddressForm(request.POST)
        if form.is_valid() and address_form.is_valid():
            user = form.save(commit=False)
            user.save()    
            address = address_form.save(commit=False)
            address.user = user
            address.save()
            
            messages.success(request, "Your account has been created!")
            return redirect('register')
    else:
        form = CustomUserCreationForm()
        address_form = AddressForm()
    
    return render(request, 'base/register.html', {'form': form, 'address_form': address_form,'hide_navbar': True})


# Login view
def user_login(request):
    if request.method == 'POST':
        form = UserAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home') 
    else:
        form = UserAuthenticationForm()

    return render(request, 'base/login.html', {'form': form, 'hide_navbar': True})

# Logout view
def user_logout(request):
    logout(request)
    # return redirect('home',{'hide_navbar': True})  # Redirect to home page after logout
    return redirect(home)  # Redirect to home page after logout