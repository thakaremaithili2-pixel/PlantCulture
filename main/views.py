from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Product, Cart, Order, OrderItem
from .forms import ProductForm

# ── Auth ──────────────────────────────────────────────

def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('products')
    error = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('products')
        else:
            error = 'Invalid username or password. Please try again.'
    return render(request, 'login.html', {'error': error})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('products')
    error = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        if not username or not password:
            error = 'Username and password are required.'
        elif User.objects.filter(username=username).exists():
            error = 'Username already taken.'
        else:
            User.objects.create_user(username=username, password=password)
            messages.success(request, f'Account created! Please login as {username}.')
            return redirect('login')
    return render(request, 'register.html', {'error': error})

def logout_view(request):
    logout(request)
    return redirect('login')

# ── Products ─────────────────────────────────────────

@login_required(login_url='/login/')
def products(request):
    category = request.GET.get('category', '')
    search = request.GET.get('search', '')
    items = Product.objects.all()
    if category:
        items = items.filter(category=category)
    if search:
        items = items.filter(name__icontains=search)
    categories = Product.objects.values_list('category', flat=True).distinct()
    return render(request, 'products.html', {
        'items': items,
        'categories': categories,
        'selected_category': category,
        'search': search,
    })

@login_required(login_url='/login/')
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added!')
            return redirect('products')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})

# ── Cart ─────────────────────────────────────────────

@login_required(login_url='/login/')
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    total = sum(item.subtotal() for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})

@login_required(login_url='/login/')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f'"{product.name}" added to cart!')
    return redirect('products')

@login_required(login_url='/login/')
def update_cart(request, item_id):
    item = get_object_or_404(Cart, id=item_id, user=request.user)
    action = request.POST.get('action')
    if action == 'increase':
        item.quantity += 1
        item.save()
    elif action == 'decrease':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
    elif action == 'remove':
        item.delete()
    return redirect('cart')

# ── Checkout / Orders ─────────────────────────────────

@login_required(login_url='/login/')
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    if not cart_items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')
    total = sum(item.subtotal() for item in cart_items)
    if request.method == 'POST':
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        if not address or not phone:
            return render(request, 'checkout.html', {
                'cart_items': cart_items, 'total': total,
                'error': 'Address and phone are required.'
            })
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user, total=total, address=address, phone=phone
            )
            for item in cart_items:
                OrderItem.objects.create(
                    order=order, product=item.product,
                    quantity=item.quantity, price=item.product.price
                )
            cart_items.delete()
        return redirect('order_success', order_id=order.id)
    return render(request, 'checkout.html', {'cart_items': cart_items, 'total': total})

@login_required(login_url='/login/')
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_success.html', {'order': order})

@login_required(login_url='/login/')
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_orders.html', {'orders': orders})
