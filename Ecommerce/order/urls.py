from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('checkout/<int:item_id>/', views.checkout, name='checkout'), # Checkout Item Page Url
    path('orders/', views.order_list, name='order_list'), # Orders Page Url
    path('view_cart/', views.view_cart, name='view_cart'), # View Cart Items Page Url
    path('add-to-cart/<str:pk>', views.add_to_cart, name='add_to_cart'), # Add Item to Cart Page Url
    path('delivered_items/', views.delivered_items, name='delivered_items'), # Delivered Items Page Url
    path('canceled_items/', views.canceled_items, name='canceled_items'), # Canceled Items Page Url
    path('order-status/<str:order_id>/', views.order_status, name='order_status'), # Order Delivery Status Page Url
    path('order-summary/<str:order_id>/', views.order_summary, name='order_summary'), # Order Summary before Checkout Page Url
    path('remove-from-cart/<str:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'), #Remove the Item from Cart
    path('mark_order_as_delivered/<str:order_id>/', views.mark_order_as_delivered, name='mark_order_as_delivered'), # Just to mark the products as Delivered
    path('mark_order_as_canceled/<str:order_id>/', views.mark_order_as_canceled, name='mark_order_as_canceled'), # Just to mark the products as Canceled

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)