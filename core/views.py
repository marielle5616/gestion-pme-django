from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction, models
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Value, Count, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal
from functools import wraps

from core.models import Company, CustomUser, Client, Invoice

# --- DECORATOR ---
def tenant_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role == 'SYSTEM_ADMIN' or request.user.is_superuser:
            return redirect('admin_dashboard')
        if not getattr(request.user, 'company_id', None):
            logout(request)
            messages.error(request, "Session invalide")
            return redirect('accueil')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# --- ACCUEIL ---
@require_http_methods(["GET", "POST"])
def accueil(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'register':
            company_name = request.POST.get('company_name', '').strip()[:255]
            email = request.POST.get('email', '').strip().lower()
            password = request.POST.get('password', '')

            if not company_name or len(company_name) < 2:
                messages.error(request, "Nom d'entreprise invalide")
                return render(request, 'accueil.html')

            try:
                validate_email(email)
                validate_password(password)
            except ValidationError as e:
                messages.error(request, " ".join(e.messages) if hasattr(e, 'messages') else str(e))
                return render(request, 'accueil.html')

            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Cet email existe déjà")
            else:
                try:
                    with transaction.atomic():
                        company = Company.objects.create(name=company_name)
                        user = CustomUser.objects.create_user(
                            username=email, email=email, password=password,
                            company=company, role='admin', full_name=company_name
                        )
                        login(request, user)
                        return redirect('dashboard')
                except Exception as e:
                    print(f"Erreur inscription: {e}")
                    messages.error(request, "Erreur création compte")

        else:
            email = request.POST.get('email', '').strip().lower()
            password = request.POST.get('password', '')
            if not email or not password:
                messages.error(request, "Email et mot de passe requis")
            else:
                user = authenticate(request, username=email, password=password)
                if user:
                    if not user.is_active:
                        messages.error(request, "Compte désactivé")
                    else:
                        login(request, user)
                        return redirect('dashboard')
                else:
                    messages.error(request, "Email ou mot de passe incorrect")

    return render(request, 'accueil.html')

def logout_view(request):
    logout(request)
    return redirect('accueil')

# --- DASHBOARD CORRIGÉ (fix InvalidOperation) ---
@tenant_required
def dashboard(request):
    company = request.user.company
    
    total_clients = Client.objects.filter(company=company).count()
    recent_invoices = Invoice.objects.filter(company=company).order_by('-created_at')[:5]
    
    # FIX ICI: output_field=DecimalField() obligatoire pour SQLite
    total_revenue = Invoice.objects.filter(company=company, status='paid').aggregate(
        total=Coalesce(Sum('total_amount'), Value(Decimal('0.00'), output_field=DecimalField(max_digits=12, decimal_places=2)))
    )['total'] or Decimal('0.00')
    
    pending_invoices = Invoice.objects.filter(company=company, status='sent').count()

    return render(request, 'tenant/dashboard.html', {
        'total_clients': total_clients,
        'recent_invoices': recent_invoices,
        'total_revenue': total_revenue,
        'pending_invoices': pending_invoices,
    })