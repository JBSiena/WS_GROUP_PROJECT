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
        
        # Search for SubCategories
        subcategories = Category.objects.filter(name__icontains=searched)
        
        # Fetch Products associated with the matched SubCategories
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
    categories = Category.objects.all()
    product_detail = get_object_or_404(Product, pk=pk)

    return render(request, 'base/product_detail.html', {
        'categories': categories,
        'product_detail': product_detail,
    })

# Add to Cart
@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    quantity = int(request.GET.get('quantity', 1))
    cart, created = ShoppingCart.objects.get_or_create(user=request.user)

    # Check if the product already exists in the cart
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if created:  
        cart_item.quantity = quantity # If the item is newly created, set the quantity directly
    else:
        cart_item.quantity += quantity  # If it already exists, update the quantity

    cart_item.save()
    messages.success(request, "Your order has been added successfully to your Cart!")
    return redirect('view_cart')

# Checkout View
@login_required
def checkout(request):
    try:
        cart = ShoppingCart.objects.get(user=request.user)
    except ShoppingCart.DoesNotExist:
        return redirect('view_cart')

    cart_items = cart.items.all()
    total_price = sum(item.total_price() for item in cart_items)
    user_address = Address.objects.filter(user=request.user).first()
    username = Customer.objects.get(id=request.user.id)

    if request.method == 'POST':
        address_form = AddressForm(request.POST)
        form = EditProfileForm(request.POST, request.FILES, instance=username)
        payment_method = request.POST['payment_method']  # Get payment method from form

        if address_form.is_valid() and payment_method and form.is_valid():
            address = address_form.save(commit=False)
            usern = form.save(commit=False)
            if user_address:
                address.id = user_address.id
                usern.id = username.id
            address.user = request.user
            usern.user = request.user
            address.save()
            usern.save()


            shipping_address = f"{address.street}, {address.purok}, {address.city}, (Landmark: {address.landmark})"

            # Create the order
            order = Order.objects.create(
                user=request.user,
                status=Order.PENDING,
                total_price=total_price,
                shipping_address=shipping_address,
            )

            # Add items to the order
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price,
                )

            # Handle payment
            if payment_method == 'COD':
                Payment.objects.create(
                    order=order,
                    payment_method=Payment.CASH_ON_DELIVERY,
                    payment_status=Payment.PENDING,
                )
            elif payment_method == 'GCASH':
                Payment.objects.create(
                    order=order,
                    payment_method=Payment.GCASH,
                    payment_status=Payment.COMPLETED,
                )
            elif payment_method == 'PAYPAL':
                Payment.objects.create(
                    order=order,
                    payment_method=Payment.PAYPAL,
                    payment_status=Payment.COMPLETED,
                )
            elif payment_method == 'PAYMAYA':
                Payment.objects.create(
                    order=order,
                    payment_method=Payment.PAYMAYA,
                    payment_status=Payment.COMPLETED,
                )

            # Set a random delivery date
            order.set_random_delivery_date()
            # Clear the cart
            cart.items.all().delete()
            return redirect('order_summary', order_id=order.id)

    else:
        address_form = AddressForm(instance=user_address)
        username = Customer.objects.get(id=request.user.id)
        form = EditProfileForm(instance=username)

    return render(request, 'base/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'address_form': address_form,
        'form': form,
        'payment_methods': ['COD', 'PAYPAL', 'PAYMAYA', 'GCASH'],  # Pass payment options to the template
    })


# Order Summary View
@login_required
def order_summary(request, order_id):
    messages.success(request, "Your order has been placed successfully!")
    order = get_object_or_404(Order, pk=order_id)
    return render(request, 'base/order_summary.html', {'order': order})

@login_required
def view_cart(request):
    try:
        cart = ShoppingCart.objects.get(user=request.user)  # Get the user's cart
        cart_items = CartItem.objects.filter(cart=cart)  # Get items in the cart
        total_price = cart.get_total_price()  # Get total price using the method
    except ShoppingCart.DoesNotExist:
        cart_items = []
        total_price = 0

    return render(request, 'base/view_cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })

@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    cart_item.delete()  # Remove the cart item
    remove = messages.error(request, "Your order has been remove successfully to your Cart!")
    return redirect('view_cart')

@login_required
def order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Update the shipping status based on the delivery date
    if hasattr(order, 'shipping'):
        order.shipping.update_shipping_status()

    return render(request, 'base/order_status.html', {
        'order': order,
        'shipping': order.shipping,
        'order_items': order.items.all(),
        'shipping_address': order.shipping_address,
    })



@login_required
def create_shipping(request, order_id):
    # Get the order by ID or return 404 if not found
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Check if shipping already exists for this order
    if not hasattr(order, 'shipping'):
        # Create a new Shipping record for this order
        shipping = Shipping.objects.create(order=order, shipping_method='Standard')
        # Set a random shipping date and automatically update order status
        shipping.set_random_shipping_date()
        
        # Provide feedback
        messages.success(request, f"Shipping has been created and the order status is now {order.status}.")
    else:
        messages.warning(request, "Shipping already exists for this order.")

    return redirect('view_order', order_id=order.id)


# View the Ordered List / Shipping Products
@login_required
def order_list(request):
    # Get all orders for the logged-in user
    orders = Order.objects.filter(user=request.user).exclude(status=Order.DELIVERED).order_by('-created_at')
    product = Product.objects.filter(name__in=orders)
    # Pass the orders to the template
    return render(request, 'base/order_list.html', {
        'orders': orders,
        'product':product,
    })


# Check if already Delivered to mark as Delivered and move to Delivered Items
def mark_order_as_delivered(request, order_id):
    # Get the order object
    order = get_object_or_404(Order, id=order_id, user=request.user)
    # Mark as delivered and move items to DeliveredItem
    if order.status != Order.DELIVERED:
        order.status = Order.DELIVERED
        order.save()
        # Move items to delivered items
        order.move_to_delivered_items()

        messages.success(request, f"Order #{order.id} marked as delivered.")
    else:
        messages.info(request, f"Order #{order.id} is already delivered.")

    return redirect('delivered_items')

# Delivered Items
@login_required
def delivered_items(request):
    delivered_orders = Order.objects.filter(status=Order.DELIVERED, user=request.user)
    return render(request, 'base/delivered_items.html', {
        'delivered_orders': delivered_orders,
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
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been created!")
            return redirect('login')  # Redirect to login page after registration
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'base/register.html', {'form': form, 'hide_navbar': True})

# Login view
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # Redirect to home page after login
    else:
        form = AuthenticationForm()

    return render(request, 'base/login.html', {'form': form, 'hide_navbar': True})

# Logout view
def user_logout(request):
    logout(request)
    # return redirect('home',{'hide_navbar': True})  # Redirect to home page after logout
    return redirect(home)  # Redirect to home page after logout