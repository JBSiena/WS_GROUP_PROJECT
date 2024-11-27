from django.db import models
from base.models import *
# Create your models here.
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
    
    def cancel_order(self):
        if self.status != Order.CANCELED:
            # Update order status
            self.status = Order.CANCELED
            self.save()

            # Cancel payment if it exists
            if hasattr(self, 'payment'):
                self.payment.cancel_payment()

            # Update shipping status if it exists
            if hasattr(self, 'shipping'):
                self.shipping.cancel_shipping()

            # Move items to canceled items
            self.move_to_canceled_items()

            return True  # Indicate success
        return False  # Already canceled, no changes made

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
            shipping_status="Not Shipped",
            shipping_date=delivery_date,
            tracking_number = random_string,
        )

        # Update order status to 'Shipped'
        self.status = Order.PENDING
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

    def move_to_canceled_items(self):
        # Ensure the order is marked as delivered
        if self.status == Order.CANCELED:
            for item in self.items.all():
                CanceledItem.objects.create(
                    order=self,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.price,
                )
                
    def save(self, *args, **kwargs):
        # Prevent status changes if the order is already canceled
        if self.pk and self.status == self.CANCELED:
            original_status = Order.objects.get(pk=self.pk).status
            if original_status == self.CANCELED and self.status != self.CANCELED:
                raise ValueError("Cannot change the status of a canceled order.")
        super().save(*args, **kwargs)

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
        return f"{self.quantity} x {self.product.name} (Size: {self.size.size})"

    def total_price(self):
        quantity = self.quantity if self.quantity is not None else 0
        price = self.product.price if self.product.price is not None else 0
        return quantity * price



# Payment Model
class Payment(models.Model):
    CASH_ON_DELIVERY = 'Cash on Delivery'
    PAYPAL = 'PayPal'
    GCASH = 'GCash'
    PAYMAYA = 'PayMaya'

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
    
    def save(self, *args, **kwargs):
        # Prevent status changes if the payment is failed (after cancellation)
        if self.pk and self.payment_status == Payment.FAILED:
            original_status = Payment.objects.get(pk=self.pk).payment_status
            if original_status == Payment.FAILED and self.payment_status != Payment.FAILED:
                raise ValueError("Cannot change the status of a failed payment.")
        super().save(*args, **kwargs)

    def cancel_payment(self):
        self.payment_status = Payment.FAILED
        self.save()


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

        if self.order.status != Order.CANCELED:
            if shipping_date <= today:
                self.shipping_status = 'Delivered'
                self.order.status = Order.DELIVERED
            elif today >= shipping_date - timedelta(days=3):
                self.shipping_status = 'Shipped'
                self.order.status = Order.SHIPPED
            else:
                self.shipping_status = 'Not Shipped'
                self.order.status = Order.PENDING
        else:
            self.shipping_status = 'Canceled'
            self.order.status = Order.CANCELED

        self.order.save()
        self.save()

    def save(self, *args, **kwargs):
        # Prevent status changes if the shipping is canceled
        if self.pk and self.shipping_status == 'Canceled':
            original_status = Shipping.objects.get(pk=self.pk).shipping_status
            if original_status == 'Canceled' and self.shipping_status != 'Canceled':
                raise ValueError("Cannot change the status of a canceled shipping.")
        super().save(*args, **kwargs)

    def cancel_shipping(self):
        self.shipping_status = 'Canceled'
        self.save()

class DeliveredItem(models.Model):
    order = models.ForeignKey(Order, related_name='delivered_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Delivered)"
    
class CanceledItem(models.Model):
    order = models.ForeignKey(Order, related_name='canceled_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Canceled)"
