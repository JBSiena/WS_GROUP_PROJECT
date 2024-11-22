from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.home, name='home'), # Main Page Url
    path('logout/', views.user_logout, name='logout'), # Logout Page Url
    path('accounts/register/', views.register, name='register'), # Register user Page Url
    path('accounts/login/', views.user_login, name='login'), # Login Page Url
    path('address/<str:pk>/', views.address, name='address'), # User Address
    path('search_product/', views.search_product, name='search_product'), # Searched Products
    path('edit_profile/<int:pk>/', views.edit_customer, name='edit_profile'), # Edit User Profile Information
    path('product_detail/<str:pk>/', views.product_detail, name='product_detail'), # Product Detail Page Url

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)