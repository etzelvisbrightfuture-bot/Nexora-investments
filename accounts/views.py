from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django import forms
from django.contrib.auth.models import User
from django.db.models import Sum
from investments.models import UserInvestment, WithdrawalRequest, UserProfile
from .forms import CustomUserCreationForm


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            ref_id = request.GET.get('ref')
            if ref_id:
                try:
                    referrer = User.objects.get(id=ref_id)
                    user.profile.referred_by = referrer
                    user.profile.save()
                except User.DoesNotExist:
                    pass
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            verification_link = f"http://127.0.0.1:8000/accounts/verify/{uid}/{token}/"
            subject = 'Verify Your Email - Nexora Investments'
            html_message = render_to_string('emails/verify_email.html', {
                'user': user,
                'verification_link': verification_link
            })
            send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message)
            messages.success(request, 'Account created! Please check your email to verify your account.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})


def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, 'Email verified successfully! Welcome to Nexora.')
        return redirect('dashboard')
    else:
        messages.error(request, 'Verification link is invalid or has expired.')
        return redirect('login')


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
        if user is not None:
            if not user.is_active:
                messages.error(request, 'Please verify your email address before logging in.')
                return redirect('login')
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard_view(request):
    investments = UserInvestment.objects.filter(user=request.user).order_by('-created_at')
    active_investments = investments.filter(status='active')
    pending_investments = investments.filter(status='pending')
    completed_investments = investments.filter(status='completed')
    total_invested = sum(inv.amount for inv in active_investments) + sum(inv.amount for inv in completed_investments)
    withdrawable_balance = sum(inv.expected_return for inv in active_investments) + sum(inv.expected_return for inv in completed_investments)
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    referral_link = f"http://127.0.0.1:8000/accounts/signup/?ref={request.user.id}"
    total_referrals = request.user.referred_users.count()
    context = {
        'investments': investments,
        'total_invested': total_invested,
        'withdrawable_balance': withdrawable_balance,
        'active_count': active_investments.count(),
        'pending_count': pending_investments.count(),
        'referral_link': referral_link,
        'referral_earnings': profile.referral_earnings,
        'total_referrals': total_referrals,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Your profile details have been updated successfully!')
            else:
                messages.error(request, 'Please correct the errors below.')
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password has been changed securely!')
            else:
                messages.error(request, 'Please correct the password errors below.')
        return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)
    return render(request, 'accounts/profile.html', {
        'user_form': user_form,
        'password_form': password_form
    })


@user_passes_test(lambda u: u.is_staff, login_url='home')
def admin_dashboard_view(request):
    total_users = User.objects.count()
    total_invested = UserInvestment.objects.filter(status__in=['active', 'completed']).aggregate(Sum('amount'))['amount__sum'] or 0
    total_withdrawn = WithdrawalRequest.objects.filter(status='approved').aggregate(Sum('amount'))['amount__sum'] or 0
    pending_investments = UserInvestment.objects.filter(status='pending').count()
    pending_withdrawals = WithdrawalRequest.objects.filter(status='pending').count()
    recent_investments = UserInvestment.objects.select_related('user', 'plan').order_by('-created_at')[:5]
    recent_withdrawals = WithdrawalRequest.objects.select_related('user').order_by('-created_at')[:5]
    context = {
        'total_users': total_users,
        'total_invested': total_invested,
        'total_withdrawn': total_withdrawn,
        'pending_investments': pending_investments,
        'pending_withdrawals': pending_withdrawals,
        'recent_investments': recent_investments,
        'recent_withdrawals': recent_withdrawals,
    }
    return render(request, 'accounts/admin_dashboard.html', context)