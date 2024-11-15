from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ShoppingCart)
admin.site.register(CartItem)
admin.site.register(Payment)
admin.site.register(Shipping)
admin.site.register(Profile)