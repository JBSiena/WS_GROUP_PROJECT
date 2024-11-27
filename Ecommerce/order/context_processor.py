from .models import CartItem, ShoppingCart

def cart_count(request):
    if request.user.is_authenticated:
        cart = ShoppingCart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        cart_count = cart_items.count()
    else:
        cart_count = 0 
    return {'cart_count': cart_count}
