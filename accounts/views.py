from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomerRegistrationForm, EmployeeCreateForm
from .models import User
from .decorators import customer_required, karyawan_required, owner_required

# Landing page
def landing_page(request):
    return render(request, 'landing.html')

# Public registration (only customer)
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'customer'
            full_name = form.cleaned_data.get('full_name', '')
            if ' ' in full_name:
                user.first_name, user.last_name = full_name.split(' ', 1)
            else:
                user.first_name = full_name
            user.phone_number = form.cleaned_data.get('phone_number')
            user.address = form.cleaned_data.get('address')
            user.save()
            login(request, user)
            messages.success(request, f'Account created! Welcome {user.username}.')
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomerRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

# Login for all roles
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('landing')

@login_required
def dashboard_redirect(request):
    if request.user.is_customer():
        return redirect('customer_dashboard')
    elif request.user.is_karyawan():
        return redirect('karyawan_dashboard')
    elif request.user.is_owner():
        return redirect('owner_dashboard')
    return redirect('login')

@customer_required
def customer_dashboard(request):
    return render(request, 'accounts/dashboard_customer.html', {'user': request.user})

@karyawan_required
def karyawan_dashboard(request):
    return render(request, 'accounts/dashboard_karyawan.html', {'user': request.user})

@owner_required
def owner_dashboard(request):
    return render(request, 'accounts/dashboard_owner.html', {'user': request.user})

@owner_required
def employee_list(request):
    employees = User.objects.filter(role='karyawan')
    return render(request, 'accounts/employee_list.html', {'employees': employees})

@owner_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'karyawan'
            user.save()
            messages.success(request, f'Employee {user.username} created.')
            return redirect('employee_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = EmployeeCreateForm()
    return render(request, 'accounts/employee_form.html', {'form': form, 'title': 'Add Employee'})

@owner_required
def employee_edit(request, pk):
    employee = get_object_or_404(User, pk=pk, role='karyawan')
    if request.method == 'POST':
        form = EmployeeCreateForm(request.POST, instance=employee)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'karyawan'
            user.save()
            messages.success(request, f'Employee {user.username} updated.')
            return redirect('employee_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = EmployeeCreateForm(instance=employee)
    return render(request, 'accounts/employee_form.html', {'form': form, 'title': 'Edit Employee'})

@owner_required
def employee_delete(request, pk):
    employee = get_object_or_404(User, pk=pk, role='karyawan')
    if request.method == 'POST':
        username = employee.username
        employee.delete()
        messages.success(request, f'Employee {username} deleted.')
        return redirect('employee_list')
    return render(request, 'accounts/employee_confirm_delete.html', {'employee': employee})