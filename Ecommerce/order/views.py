from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from base.forms import *
from order.models import *

# Add to Cart
@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    quantity = int(request.GET.get('quantity', 1))
    cart, created = ShoppingCart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if created:
        cart_item.quantity = quantity
    else:
        cart_item.quantity += quantity

    cart_item.save()

    if request.GET.get('checkout') == 'true':
        return redirect('checkout', item_id=cart_item.id)

    messages.success(request, "Your order has been added successfully to your Cart!")
    return redirect('view_cart')


# Checkout View
@login_required
def checkout(request,item_id):
    try:
        cart = ShoppingCart.objects.get(user=request.user)
    except ShoppingCart.DoesNotExist:
        return redirect('view_cart')

    cart_items = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    total_price = cart_items.total_price()
    user_address = Address.objects.filter(user=request.user).first()
    username = Customer.objects.get(id=request.user.id)

    if request.method == 'POST':
        address_form = AddressForm(request.POST)
        form = EditProfileForm(request.POST, request.FILES, instance=username)
        payment_method = request.POST.get('payment_method')   # Get payment method from form

        if not payment_method:
            return redirect('checkout', item_id=item_id)

        if address_form.is_valid() and payment_method and form.is_valid():
            address = address_form.save(commit=False)
            user = form.save(commit=False)
            if user_address:
                address.id = user_address.id
                user.id = username.id
            address.user = request.user
            user.user = request.user
            address.save()
            user.save()


            shipping_address = f"{address.street}, {address.purok}, {address.city}, (Landmark: {address.landmark})"

            # Create the order
            order = Order.objects.create(
                user=request.user,
                status=Order.PENDING,
                total_price=total_price,
                shipping_address=shipping_address,
            )

            # Add items to the order
            
            OrderItem.objects.create(
                order=order,
                product=cart_items.product,
                quantity=cart_items.quantity,
                price=cart_items.product.price,
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
            cart_items.delete()
            return redirect('order_summary', order_id=order.id)

    else:
        address_form = AddressForm(instance=user_address)
        form = EditProfileForm(instance=username)

    return render(request, 'order/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'address_form': address_form,
        'form': form,
        'payment_methods': ['COD', 'PAYPAL', 'PAYMAYA', 'GCASH'],
    })


# Order Summary View
@login_required
def order_summary(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    if request.method == 'POST' and 'cancel_order' in request.POST:
        if order.status == Order.PENDING:  # Only allow cancellation for pending orders
            if order.cancel_order():
                messages.success(request, f"Order #{order.id} has been canceled successfully.")
            else:
                messages.error(request, "Failed to cancel the order.")
            return redirect('order_list')
        else:
            messages.error(request, "Order cannot be canceled as it is not in a pending state.")

    return render(request, 'order/order_summary.html', {'order': order})


@login_required
def view_cart(request):
    try:
        cart = ShoppingCart.objects.get(user=request.user)  # Get the user's cart
        cart_items = CartItem.objects.filter(cart=cart)  # Get items in the cart
        total_price = cart.get_total_price()  # Get total price using the method
    except ShoppingCart.DoesNotExist:
        cart_items = []
        total_price = 0

    return render(request, 'order/view_cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
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

    return render(request, 'order/order_status.html', {
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
    orders = Order.objects.filter(user=request.user).exclude(status=Order.DELIVERED and Order.CANCELED).order_by('-created_at')
    product = Product.objects.filter(name__in=orders)
    # Pass the orders to the template
    return render(request, 'order/order_list.html', {
        'orders': orders,
        'product':product,
    })


# Check if already Delivered to mark as Delivered and move to Delivered Items
def mark_order_as_canceled(request, order_id):
    # Get the order object
    order = get_object_or_404(Order, id=order_id, user=request.user)
    # Mark as delivered and move items to DeliveredItem
    if order.status == Order.CANCELED:
        order.save()
        # Move items to delivered items
        order.move_to_canceled_items()

        messages.success(request, f"Order #{order.id} marked as canceled.")
    else:
        messages.info(request, f"Order #{order.id} is already canceled.")

    return redirect('canceled_items')

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
    return render(request, 'order/delivered_items.html', {
        'delivered_orders': delivered_orders,
    })

@login_required
def canceled_items(request):
    canceled_orders = Order.objects.filter(status=Order.CANCELED, user=request.user)
    return render(request, 'order/canceled_items.html', {
        'canceled_orders': canceled_orders,
    })