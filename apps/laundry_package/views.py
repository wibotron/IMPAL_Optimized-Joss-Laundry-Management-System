from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import owner_required
from .models import LaundryPackage
from .forms import PackageForm
# create your views here.

@login_required
def package_list(request):
    is_owner = request.user.is_owner() 
    if is_owner:
        # Owner bisa melihat paket non-aktif untuk di-maintenance
        packages = LaundryPackage.objects.all()
    else:
        # Customer/Karyawan hanya melihat paket yang siap pakai
        packages = LaundryPackage.objects.active_and_valid()
    return render(request, 'packages/package_list.html', {
        'packages': packages,
        'is_owner': is_owner
    })

@login_required
@owner_required
def package_create(request):
    if request.method == 'POST':
        form = PackageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Paket baru berhasil dibuat.")
            return redirect('packages:package_list')
    else:
        form = PackageForm()
    return render(request, 'packages/package_form.html', {'form': form, 'title': 'Tambah Paket'})

@login_required
@owner_required
def package_update(request, pk):
    package = get_object_or_404(LaundryPackage, pk=pk)
    if request.method == 'POST':
        form = PackageForm(request.POST, instance=package)
        if form.is_valid():
            form.save()
            messages.success(request, f"Paket {package.name} diperbarui.")
            return redirect('packages:package_list')
    else:
        form = PackageForm(instance=package)
    return render(request, 'packages/package_form.html', {'form': form, 'title': 'Edit Paket'})

@login_required
@owner_required
def package_delete(request, pk):
    package = get_object_or_404(LaundryPackage, pk=pk)
    if request.method == 'POST':
        package.delete()
        messages.success(request, "Paket berhasil dihapus.")
        return redirect('packages:package_list')
    return render(request, 'packages/package_confirm_delete.html', {'package': package})