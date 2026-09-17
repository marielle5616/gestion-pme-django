from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction
from core.models import Company, CustomUser

def accueil(request):
    # ON NE REDIRIGE PLUS AUTOMATIQUEMENT - on affiche toujours l'accueil
    if request.method == 'POST':
        if 'company_name' in request.POST:
            company_name = request.POST.get('company_name','').strip()
            email = request.POST.get('email','').strip().lower()
            password = request.POST.get('password','')

            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Cet email existe déjà")
            else:
                with transaction.atomic():
                    company = Company.objects.create(name=company_name)
                    user = CustomUser(username=email, email=email, company=company, role='ADMIN', full_name=company_name)
                    user.set_password(password)
                    user.save()
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    messages.success(request, "Compte créé !")
                    return redirect('tenant_dashboard')
        else:
            email = request.POST.get('email','').strip().lower()
            password = request.POST.get('password','')
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                return redirect('tenant_dashboard')
            else:
                messages.error(request, "Email ou mot de passe incorrect")

    return render(request, 'accueil.html')

def logout_view(request):
    logout(request)
    return redirect('accueil')