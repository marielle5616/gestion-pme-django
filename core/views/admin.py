from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.views.decorators.http import require_http_methods
from functools import wraps
from core.models import Company, CustomUser

# SEUL le superuser peut être sysadmin
def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accueil')
        # ✅ SEULEMENT superuser = sysadmin
        if not request.user.is_superuser:
            messages.error(request, "Accès interdit : admin système uniquement.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@admin_required
def admin_dashboard(request):
    companies = Company.objects.annotate(user_count=Count('users')).order_by('-created_at')
    total_companies = companies.count()
    total_users = CustomUser.objects.filter(is_superuser=False).count()
    
    plans_count = {
        'starter': companies.filter(plan='starter').count(),
        'business': companies.filter(plan='business').count(),
        'enterprise': companies.filter(plan='enterprise').count()
    }
    
    context = {
        'companies': companies[:5],
        'total_companies': total_companies,
        'total_users': total_users,
        'plans_count': plans_count
    }
    return render(request, 'admin/dashboard.html', context)

@admin_required
@require_http_methods(["GET", "POST"])
def admin_companies(request):
    companies = Company.objects.annotate(user_count=Count('users')).order_by('-created_at')
    
    # ✅ Modifications uniquement en POST
    if request.method == 'POST':
        action = request.POST.get('action')
        company_id = request.POST.get('id')
        company = get_object_or_404(Company, id=company_id)
        
        if action == 'update_plan':
            plan = request.POST.get('plan')
            if plan in ['starter', 'business', 'enterprise']:
                company.plan = plan
                company.save()
                messages.success(request, f"Plan {company.name} -> {plan}")
            else:
                messages.error(request, "Plan invalide")
                
        elif action == 'update_status':
            status = request.POST.get('status')
            if status in ['active', 'inactive', 'suspended']:
                company.subscription_status = status
                company.save()
                messages.success(request, f"Statut {company.name} -> {status}")
            else:
                messages.error(request, "Statut invalide")
                
        return redirect('admin_companies')
        
    plans_count = {
        'total': companies.count(),
        'active': companies.filter(subscription_status='active').count(),
        'starter': companies.filter(plan='starter').count(),
        'business': companies.filter(plan='business').count(),
        'enterprise': companies.filter(plan='enterprise').count()
    }
    return render(request, 'admin/companies.html', {'companies': companies, 'plans_count': plans_count})

@admin_required
def admin_company_detail(request, pk):
    company = get_object_or_404(Company, pk=pk)
    company_users = company.users.select_related('company').all()
    return render(request, 'admin/company_detail.html', {'company': company, 'company_users': company_users})

@admin_required
def admin_users(request):
    users = CustomUser.objects.select_related('company').filter(is_superuser=False).order_by('-date_joined')
    return render(request, 'admin/users.html', {'users': users})

@admin_required
def admin_settings(request):
    return render(request, 'admin/settings.html')