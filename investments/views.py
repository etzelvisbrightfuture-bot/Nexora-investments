from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from .models import InvestmentPlan, UserInvestment, WithdrawalRequest

def investment_plans(request):
    """Display all available investment plans in a specific custom order"""
    plans = InvestmentPlan.objects.filter(is_active=True)
    
    ordered_categories = [
        ('crypto', 'CRYPTO'),
        ('forex', 'FOREX'),
        ('tesla', 'TESLA'),
        ('ai', 'AI'),
        ('spacex', 'SPACEX'),
    ]
    
    return render(request, 'investments/plans.html', {
        'plans': plans,
        'ordered_categories': ordered_categories
    })

@login_required
def invest_in_plan(request, plan_id):
    """Handle investment in a specific plan via Crypto or Gift Card"""
    plan = get_object_or_404(InvestmentPlan, id=plan_id, is_active=True)
    
    WALLETS = {
        'solana': "CoakgcBt2r9wFkGjpAJqUbsRHWGGh7QE4YZKSKGQLEAC",
        'bitcoin': "bc1qtzy9pzmpyeyp7waqkdjjzlrhj4kfsstdzwmf8k",
        'ethereum': "0x83baf08973dc6e2352e7ac36577ba65a4b8502e6",
    }
    
    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        method = request.POST.get('payment_method')
        image = request.FILES.get('payment_proof')
        
        if not amount_str or not method:
            messages.error(request, 'Please enter an amount and select a payment method.')
            return render(request, 'investments/invest.html', {'plan': plan, 'wallets': WALLETS})
        
        amount = Decimal(amount_str)
        
        if amount < plan.minimum_amount or amount > plan.maximum_amount:
            messages.error(request, f'Amount must be between ${plan.minimum_amount} and ${plan.maximum_amount}.')
            return render(request, 'investments/invest.html', {'plan': plan, 'wallets': WALLETS})

        if not image:
            messages.error(request, 'Please upload a screenshot of your payment or gift card.')
            return render(request, 'investments/invest.html', {'plan': plan, 'wallets': WALLETS})

        # 1. Create the investment in the database
        new_investment = UserInvestment.objects.create(
            user=request.user,
            plan=plan,
            amount=amount,
            payment_method=method,
            payment_proof=image,
            status='pending'
        )
        
        # 2. Send Immediate Confirmation Email
        if request.user.email:
            from django.core.mail import send_mail
            from django.conf import settings
            from django.template.loader import render_to_string
            
            subject = 'Investment Received: Pending Verification'
            html_message = render_to_string('emails/investment_pending.html', {
                'user': request.user,
                'plan': plan,
                'amount': amount
            })
            send_mail(
                subject, 
                '', 
                settings.DEFAULT_FROM_EMAIL, 
                [request.user.email], 
                html_message=html_message
            )
        
        messages.success(request, 'Investment submitted successfully! Check your email for confirmation. Admin will verify your payment shortly.')
        return redirect('dashboard')
    
    return render(request, 'investments/invest.html', {'plan': plan, 'wallets': WALLETS})

@login_required
def request_withdrawal(request):
    """Handle user withdrawal requests with balance validation"""
    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        method = request.POST.get('payment_method')
        address = request.POST.get('wallet_address')
        
        if not amount_str or not method or not address:
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'investments/withdraw.html')
        
        amount = Decimal(amount_str)
        
        if amount <= 0:
            messages.error(request, 'Withdrawal amount must be greater than zero.')
            return render(request, 'investments/withdraw.html')

        # Calculate user's current withdrawable balance
        active_investments = UserInvestment.objects.filter(user=request.user, status='active')
        completed_investments = UserInvestment.objects.filter(user=request.user, status='completed')
        
        withdrawable_balance = sum(inv.expected_return for inv in active_investments) + sum(inv.expected_return for inv in completed_investments)

        # VALIDATION: Check if they have enough balance
        if amount > withdrawable_balance:
            messages.error(request, f'Insufficient funds. Your available withdrawable balance is ${withdrawable_balance:.2f}.')
            return render(request, 'investments/withdraw.html')

        WithdrawalRequest.objects.create(
            user=request.user,
            amount=amount,
            payment_method=method,
            wallet_address=address,
            status='pending'
        )
        
        messages.success(request, 'Withdrawal request submitted successfully! Admin will process it shortly.')
        return redirect('dashboard')
    
    return render(request, 'investments/withdraw.html')