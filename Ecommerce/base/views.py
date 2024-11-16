from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import *
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import *

# Home Page - Show all products
def home(request):
    categories = Category.objects.all()
    products = Product.objects.get(is_active=True)
    return render(request, 'base/home.html', {'categories': categories, 'products': products})



# Product Detail
def product_detail(request, pk):
    # Check if the user is logged in and if not redirect to login page
    if request.user.is_authenticated:
        product = get_object_or_404(Product, pk=pk)
        return render(request, 'base/product_detail.html', {'product': product})
    else:
        return redirect('login')

# Add to Cart
@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart, created = ShoppingCart.objects.get_or_create(user=request.user)
    
    # Check if the product already exists in the cart
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:  # If it already exists, increase the quantity
        cart_item.quantity += 1
    cart_item.save()
    return redirect('cart')
 

# Shopping Cart View
@login_required
def cart(request):
    cart = ShoppingCart.objects.get(user=request.user)
    items = CartItem.objects.filter(cart=cart)
    total_price = cart.get_total_price()
    return render(request, 'base/cart.html', {'cart': cart, 'items': items, 'total_price': total_price})

# Checkout View
@login_required
def checkout(request):
    # Get the user's shopping cart
    try:
        cart = ShoppingCart.objects.get(user=request.user)
    except ShoppingCart.DoesNotExist:
        # If no cart exists for the user redirect to view_cart
        return redirect('view_cart')
    
    # Get all cart items for user's cart example get the cart items for "jbsiena" or user logged in
    cart_items = cart.items.all()

    # Calculate the total price of the items in the cart
    total_price = sum(item.total_price() for item in cart_items)


    # Pass the cart items and total price to the template
    return render(request, 'base/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })

# Order Summary View
@login_required
def order_summary(request, order_id):
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
    return redirect('view_cart')

@login_required
def order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Get associated shipping and order items
    shipping = order.shipping
    order_items = order.items.all()

    return render(request, 'base/order_status.html', {
        'order': order,
        'shipping': shipping,
        'order_items': order_items,
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

@login_required
def update_shipping_status(request):
    # Get all orders that are shipped and update their status
    shipped_orders = Shipping.objects.filter(shipping_status='Shipped')

    for shipping in shipped_orders:
        shipping.update_shipping_status()

    messages.success(request, "Shipping statuses have been updated!")
    return redirect('delivered_items')

@login_required
def place_order(request):
    try:
        # Get the user's shopping cart
        cart = ShoppingCart.objects.get(user=request.user)
    except ShoppingCart.DoesNotExist:
        messages.error(request, "No cart found.")
        return redirect('view_cart')

    cart_items = cart.items.all()

    # Create the order
    order = Order.objects.create(
        user=request.user,
        status=Order.PENDING,  # Set initial order status to 'PENDING'
        total_price=sum(item.total_price() for item in cart_items),
        shipping_address="Temporary address",  # You can ask the user to enter the address
    )

    # Add items to the order
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price,
        )

    # Create a payment (just a placeholder for now)
    Payment.objects.create(
        order=order,
        payment_method="Credit Card",  # Placeholder for payment method
        payment_status="Pending",
    )

    # Create a shipping record with a random delivery date and update order status
    order.set_random_delivery_date()
    
    # Remove The Place Ordered Item and Add to Order List
    cart.items.all().delete()

    messages.success(request, "Your order has been placed successfully!")
    return redirect('order_summary', order_id=order.id)

@login_required
def view_order_products(request, order_id):
    # Get the order object by order_id (ensure it's the logged-in user’s order)
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Get all the items in the order
    order_items = order.items.all()

    # Pass the order, order items, and shipping details to the template
    return render(request, 'base/order_products.html', {
        'order': order,
        'order_items': order_items
    })

@login_required
def order_list(request):
    # Get all orders for the logged-in user
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Pass the orders to the template
    return render(request, 'base/order_list.html', {
        'orders': orders
    })

@login_required
def mark_order_as_delivered(request, order_id):
    # Get the order object
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Update the order status to delivered
    order.status = Order.DELIVERED
    order.save()

@login_required
def delivered_items(request):
    # Get all orders for the logged-in user that are marked as 'Delivered'
    delivered_orders = Order.objects.filter(user=request.user, status=Order.DELIVERED)

    # If the user has no delivered orders
    if not delivered_orders:
        return render(request, 'base/delivered_items.html', {
            'message': 'You have no delivered orders yet.',
        })

    # Otherwise, pass the orders to the template
    return render(request, 'base/delivered_items.html', {
        'delivered_orders': delivered_orders,
    })

# Edit User Profile
@login_required
def edit_profile(request,pk):
    if request.method == 'POST':
        user = Profile.objects.get(user=request.user, id=pk)
        form = EditProfileForm(request.POST, request.FILES, instance=user)
        
        if form.is_valid():
            form.save() # Save the New User Image
            return redirect('home')

    else:
        user = Profile.objects.get(user=request.user, id=pk)
        form = EditProfileForm(instance=user)

    return render(request, 'base/edit_profile.html', {'form': form})

@login_required
def address(request,pk):
    if request.method == 'POST':
        user = Profile.objects.get(id=pk)
        form = AddressForm(request.POST, instance=user)
        
        if form.is_valid():
            form.save() # Save the New User Image
            return redirect('home')

    else:
        user = Profile.objects.get(user=request.user, id=pk)
        form = AddressForm(instance=user)

    return render(request, 'base/address.html', {'form': form})


# Register view
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            Profile.objects.create(user=user)
            messages.success(request, "Your account has been created!")
            return redirect('login')  # Redirect to login page after registration
    else:
        form = RegisterForm()
    
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
    return redirect('home')  # Redirect to home page after logout