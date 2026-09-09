from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from decimal import Decimal
from .models import InvestmentPlan, UserInvestment, WithdrawalRequest

@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'min_return', 'max_return', 'minimum_amount', 'maximum_amount', 'duration_days', 'is_active']
    list_filter = ['category', 'is_active']

@admin.register(UserInvestment)
class UserInvestmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'amount', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'plan__category']
    readonly_fields = ['payment_proof']

    def save_model(self, request, obj, form, change):
        old_obj = UserInvestment.objects.get(pk=obj.pk) if change else None
        super().save_model(request, obj, form, change)
        
        # If status changed to 'active', send email AND award referral bonus
        if change and old_obj and old_obj.status != 'active' and obj.status == 'active':
            
            # 1. Send Approval Email
            if obj.user.email:
                subject = 'Your Investment has been Approved!'
                html_message = render_to_string('emails/investment_approved.html', {
                    'user': obj.user, 
                    'plan': obj.plan, 
                    'amount': obj.amount
                })
                send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [obj.user.email], html_message=html_message)

            # 2. Award 5% Referral Bonus
            try:
                profile = obj.user.profile
                if profile.referred_by:
                    bonus = obj.amount * Decimal('0.05') # 5% bonus
                    referrer_profile = profile.referred_by.profile
                    referrer_profile.referral_earnings += bonus
                    referrer_profile.save()
            except Exception as e:
                print(f"Referral bonus error: {e}")

@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'payment_method', 'wallet_address', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    list_editable = ['status']

    def save_model(self, request, obj, form, change):
        old_obj = WithdrawalRequest.objects.get(pk=obj.pk) if change else None
        super().save_model(request, obj, form, change)
        
        # If status changed to 'approved' or 'rejected', send email
        if change and old_obj and old_obj.status != obj.status and obj.status in ['approved', 'rejected']:
            if obj.user.email:
                subject = f'Withdrawal Request {obj.status.title()}'
                html_message = render_to_string('emails/withdrawal_processed.html', {
                    'user': obj.user, 
                    'amount': obj.amount,
                    'status': obj.status
                })
                send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [obj.user.email], html_message=html_message)