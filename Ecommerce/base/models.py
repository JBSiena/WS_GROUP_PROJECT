from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.timezone import now
from datetime import timedelta
import random, string

# Creating Custom User / Permissions
class CustomUserManagement(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('You did not enter a valid email.')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    
    # for creating in superuser; use the email and password for logging in
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


# Customer Models
class Customer(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=12)
    email = models.EmailField(unique=True)
    image = models.ImageField(upload_to='images/user/', blank=True, default='images/user/dp.png')

    is_active = models.BooleanField(default=True) 
    is_staff = models.BooleanField(default=False) # Not Allowed the customer to login into backend

    objects = CustomUserManagement()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    
class Address(models.Model):
    user = models.OneToOneField(Customer, on_delete=models.CASCADE)
    street = models.CharField(max_length=100, blank=False)
    city = models.CharField(max_length=100, blank=False)
    purok = models.CharField(max_length=100, blank=False)
    landmark = models.TextField(max_length=300, blank=True)

    def __str__(self):
        return f'{self.street}, {self.purok}, {self.city}, {self.landmark}'

    
# Category Model
class Category(models.Model):
    name = models.CharField(max_length=255) # Name of the Category
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Categories' # Just to change 'Category' to 'Categories' in backend


# Product Model
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='images/products/', null=True, blank=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE, default=1)
    on_trend = models.BooleanField(default=False)
    is_activer = models.BooleanField(default=True)

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

    user = models.ForeignKey(Customer, related_name='orders', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, default=PENDING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

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
        random_days = random.randint(3, 7)
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
    
    def move_to_delivered_items(self):
        # Ensure the order is marked as delivered
        if self.status == Order.DELIVERED:
            for item in self.items.all():
                DeliveredItem.objects.create(
                    order=self,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.price,
                )

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
    user = models.OneToOneField(Customer, related_name='cart', on_delete=models.CASCADE)
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
    CASH_ON_DELIVERY = 'COD'
    PAYPAL = 'PAYPAL'
    GCASH = 'GCASH'
    PAYMAYA = 'PAYMAYA'

    PAYMENT_METHOD_CHOICES = [
        (CASH_ON_DELIVERY, 'Cash on Delivery'),
        (PAYPAL, 'PayPal'),
        (GCASH, 'GCash'),
        (PAYMAYA, 'PayMaya'),
    ]

    PENDING = 'PENDING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'

    PAYMENT_STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    ]

    order = models.OneToOneField(Order, related_name='payment', on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default=CASH_ON_DELIVERY)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default=PENDING)
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
        # Get today's date and the shipping date
        today = now().date()
        shipping_date = self.shipping_date.date() if self.shipping_date else None

        if shipping_date:
            if shipping_date <= today:
                self.shipping_status = 'Delivered'
                self.order.status = Order.DELIVERED
            elif shipping_date > today:
                self.shipping_status = 'Shipped'
                self.order.status = Order.SHIPPED
            else:
                self.shipping_status = 'Not Shipped'
                self.order.status = Order.PENDING

            self.order.save()
            self.save()

class DeliveredItem(models.Model):
    order = models.ForeignKey(Order, related_name='delivered_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Delivered)"
