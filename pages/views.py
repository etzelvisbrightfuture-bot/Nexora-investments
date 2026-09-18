from django.shortcuts import render

def home(request):
    return render(request, 'pages/home.html')
from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings

def test_email_view(request):
    # REPLACE THIS WITH YOUR ACTUAL EMAIL ADDRESS
    recipient_email = "nexoragroups01@gmail.com" 
    
    try:
        send_mail(
            subject='Nexora Test Email',
            message='If you see this, your email system is working perfectly!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False, # This forces Django to show us the exact error if it fails
        )
        return HttpResponse("✅ SUCCESS! Email sent. Check your inbox and spam folder.")
    except Exception as e:
        return HttpResponse(f"❌ FAILED! The error is: {e}")
    
def about_view(request):
    return render(request, 'pages/about.html')

def contact_view(request):
    return render(request, 'pages/contact.html')

def faq_view(request):
    return render(request, 'pages/faq.html')

def terms_view(request):
    return render(request, 'pages/terms.html')

def privacy_view(request):
    return render(request, 'pages/privacy.html')