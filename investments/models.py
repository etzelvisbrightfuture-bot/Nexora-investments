from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class InvestmentPlan(models.Model):
    CATEGORY_CHOICES = [
        ('crypto', 'CRYPTO'),
        ('forex', 'FOREX'),
        ('tesla', 'TESLA'),
        ('ai', 'AI'),
        ('spacex', 'SPACEX'),
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='crypto')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    minimum_amount = models.DecimalField(max_digits=15, decimal_places=2)
    maximum_amount = models.DecimalField(max_digits=15, decimal_places=2)
    min_return = models.DecimalField(max_digits=5, decimal_places=2, help_text="Min projected return %")
    max_return = models.DecimalField(max_digits=5, decimal_places=2, help_text="Max projected return %")
    duration_days = models.IntegerField(help_text="Investment duration in days")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    class Meta:
        verbose_name_plural = "Investment Plans"
        ordering = ['category', 'minimum_amount']


class UserInvestment(models.Model):
    PAYMENT_METHODS = [
        ('solana', 'Solana (SOL)'),
        ('bitcoin', 'Bitcoin (BTC)'),
        ('ethereum', 'Ethereum (ETH)'),
        ('giftcard', 'Gift Card'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments')
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='solana')
    
    payment_proof = models.ImageField(upload_to='payment_proofs/', blank=True, null=True, help_text="Screenshot of crypto transfer or gift card image")
    
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    expected_return = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Verification'),
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} - ${self.amount}"

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = timezone.now() + timezone.timedelta(days=self.plan.duration_days)
        
        if not self.expected_return:
            # Safely convert to Decimal to prevent float * Decimal TypeError
            amt = Decimal(str(self.amount))
            ret = Decimal(str(self.plan.min_return))
            self.expected_return = amt + (amt * ret / Decimal('100'))
            
        super().save(*args, **kwargs)
        
class WithdrawalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=50, help_text="e.g., Solana, Bitcoin, Ethereum, Bank Transfer")
    wallet_address = models.CharField(max_length=255, help_text="The address to receive the funds")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True, null=True, help_text="Optional note from admin if rejected")

    def __str__(self):
        return f"{self.user.username} - Withdrawal of ${self.amount} ({self.status})"

    class Meta:
        ordering = ['-created_at']
        
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone
from decimal import Decimal

@login_required
def request_withdrawal(request):
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

        # Optional: You can add logic here to check if they have enough 'active' or 'completed' balance
        # For now, we will allow the request and let the admin verify their balance.

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

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='referred_users')
    referral_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)