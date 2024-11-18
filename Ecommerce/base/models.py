from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random, string


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, default='Guest')
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, default='User')
    phone_number = models.CharField(max_length=20)
    image = models.ImageField(upload_to='images/user/', blank=True, default='images/user/dp.png')

    def __str__(self):
        return f'{ self.last_name }, { self.first_name } { self.middle_name }.'

    
class Address(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    street = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    purok = models.CharField(max_length=100)
    landmark = models.TextField(max_length=300, blank=True)

    
# Category Model
class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subcategories')
    
    def __str__(self):
        return self.name


# Product Model
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def is_in_stock(self):
        return self.stock > 0


# Order Model
class Order(models.Model):
    PENDING = 'PENDING'
    SHIPPED = 'SHIPPED'
    DELIVERED = 'DELIVERED'
    CANCELED = 'CANCELED'

    ORDER_STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (SHIPPED, 'Shipped'),
        (DELIVERED, 'Delivered'),
        (CANCELED, 'Canceled'),
    ]

    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, default=PENDING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.status}"

    def update_total(self):
        self.total_price = sum(item.total_price() for item in self.items.all())
        self.save()

    def set_random_delivery_date(self):
        # Set a random delivery date within 1 to 3 days from order creation date.
        if self.status != Order.PENDING:
            return  # Do nothing if the order is not in a 'PENDING' state.

        # Generate a random number of days between 3 and 7 days
        random_days = random.randint(1, 2)
        delivery_date = self.created_at + timedelta(days=random_days)

        # Generate a random code for tracking_number
        characters = string.ascii_letters + string.digits
        random_string = ''.join(random.choice(characters) for _ in range(8))

        # Create the shipping record and update order status
        shipping = Shipping.objects.create(
            order=self,
            shipping_method="Standard",
            shipping_status="Shipped",
            shipping_date=delivery_date,
            tracking_number = random_string,
        )

        # Update order status to 'Shipped'
        self.status = Order.SHIPPED
        self.save()

        return shipping

# OrderItem Model (links Order and Product)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def total_price(self):
        return self.quantity * self.price


# ShoppingCart Model (for saving user cart before checkout)
class ShoppingCart(models.Model):
    user = models.OneToOneField(User, related_name='cart', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    def get_total_price(self):
        return sum(item.total_price() for item in self.items.all())


# CartItem Model (links Product and ShoppingCart)
class CartItem(models.Model):
    cart = models.ForeignKey(ShoppingCart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='cart_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def total_price(self):
        quantity = self.quantity if self.quantity is not None else 0
        price = self.product.price if self.product.price is not None else 0
        return quantity * price


# Payment Model
class Payment(models.Model):
    order = models.OneToOneField(Order, related_name='payment', on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=50)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.payment_status}"


# Shipping Model
class Shipping(models.Model):
    order = models.OneToOneField(Order, related_name='shipping', on_delete=models.CASCADE)
    shipping_method = models.CharField(max_length=255)
    shipping_status = models.CharField(max_length=50, default='Not Shipped')
    tracking_number = models.CharField(max_length=255, null=True, blank=True)
    shipping_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Shipping for Order #{self.order.id} - {self.shipping_status}"
    
    def update_shipping_status(self):
        # Update shipping status based on the delivery date.
        if self.shipping_date and timezone.now() == self.shipping_date:
            self.shipping_status = 'Delivered'
            self.save()
    
    def get_products(self):
            # Return a list of products associated with this shipping's order
            return self.order.items.all()
    
    
