from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.timezone import now
from datetime import timedelta
import random, string

# Creating Custom User / Permissions
class CustomUserManagement(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('You did not enter a valid email or username.')
        
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
    username = models.CharField(max_length=50, blank=True, unique=True, null=True)
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
    postal = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return f'{self.street}, {self.purok}, {self.city}, {self.region}'

    
# Category Model
class Category(models.Model):
    name = models.CharField(max_length=100) 
    image = models.ImageField(upload_to='images/logo', null=True, blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Categories'

# Product Model
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='images/products/', null=True, blank=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE, default=1)
    on_trend = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def is_in_stock(self):
        return self.stock > 0
    
# Size
class Size(models.Model):
    product = models.ForeignKey(Product, related_name='sizes', on_delete=models.CASCADE)
    size = models.CharField(max_length=10)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.size

    def is_in_stock(self):
        return self.stock > 0