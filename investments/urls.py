from django.urls import path
from . import views

urlpatterns = [
    path('', views.investment_plans, name='investment_plans'),
    path('invest/<int:plan_id>/', views.invest_in_plan, name='invest_in_plan'),
    path('withdraw/', views.request_withdrawal, name='request_withdrawal'),
]