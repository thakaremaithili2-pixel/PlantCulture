from .models import Cart

def cart_count(request):
    if request.user.is_authenticated:
        count = Cart.objects.filter(user=request.user).values_list('quantity', flat=True)
        return {'cart_count': sum(count)}
    return {'cart_count': 0}
