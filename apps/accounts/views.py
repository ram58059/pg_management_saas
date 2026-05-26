from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import OwnerLoginForm, TenantLoginForm

def landing_page(request):
    if request.user.is_authenticated:
        if request.user.is_owner():
            return redirect('owner_dashboard')
        elif request.user.is_tenant():
            return redirect('tenant_dashboard')
    return render(request, 'landing.html')

def owner_login(request):
    if request.user.is_authenticated and request.user.is_owner():
        return redirect('owner_dashboard')
        
    if request.method == 'POST':
        form = OwnerLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_owner():
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name}!")
                return redirect('owner_dashboard')
            else:
                messages.error(request, "This account does not have Owner privileges.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = OwnerLoginForm()
        
    return render(request, 'owner/login.html', {'form': form})

def tenant_login(request):
    if request.user.is_authenticated and request.user.is_tenant():
        return redirect('tenant_dashboard')
        
    if request.method == 'POST':
        form = TenantLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_tenant():
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name}!")
                return redirect('tenant_dashboard')
            else:
                messages.error(request, "This account does not have Tenant privileges.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = TenantLoginForm()
        
    return render(request, 'tenant/login.html', {'form': form})

def logout_user(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('landing')
