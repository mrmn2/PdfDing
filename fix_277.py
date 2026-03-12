# pdfding/admin/views.py

from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django_otp.plugins.otp_totp.models import TOTPDevice

@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if username and email and password:
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, 'User added successfully.')
            return redirect('admin_user_list')
        else:
            messages.error(request, 'Please fill all fields.')
    return render(request, 'admin/add_user.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def change_password(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password changed successfully.')
            return redirect('admin_user_list')
    else:
        form = PasswordChangeForm(user)
    return render(request, 'admin/change_password.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def deactivate_mfa(request, user_id):
    user = get_object_or_404(User, id=user_id)
    mfa_device = TOTPDevice.objects.filter(user=user).first()
    if mfa_device:
        mfa_device.delete()
        messages.success(request, 'MFA deactivated successfully.')
    else:
        messages.error(request, 'MFA not active for this user.')
    return redirect('admin_user_list')