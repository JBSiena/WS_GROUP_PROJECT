from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.home, name='home'), # Main Page Url
    path('cart/', views.cart, name='cart'), # Cart Page Url
    path('logout/', views.user_logout, name='logout'), # Logout Page Url
    path('checkout/', views.checkout, name='checkout'), # Checkout Item Page Url
    path('register/', views.register, name='register'), # Register user Page Url
    path('orders/', views.order_list, name='order_list'), # Orders Page Url
    path('view_cart/', views.view_cart, name='view_cart'), # View Cart Items Page Url
    path('accounts/login/', views.user_login, name='login'), # Login Page Url
    path('place_order/', views.place_order, name='place_order'), # Place Order Page Url
    path('add-to-cart/<str:pk>', views.add_to_cart, name='add_to_cart'), # Add Item to Cart Page Url
    path('product/<str:pk>/', views.product_detail, name='product_detail'), # Product Detail Page Url
    path('delivered_items/', views.delivered_items, name='delivered_items'), # Delivered Items Page Url
    path('order-status/<str:order_id>/', views.order_status, name='order_status'), # Order Delivery Status Page Url
    path('order-summary/<str:order_id>/', views.order_summary, name='order_summary'), # Order Summary before Checkout Page Url
    path('remove-from-cart/<str:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'), #Remove the Item from Cart
    path('mark_order_as_delivered/<str:order_id>/', views.mark_order_as_delivered, name='mark_order_as_delivered'),
    path('<int:pk>/', views.edit_profile, name='edit_profile'),

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)