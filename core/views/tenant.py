from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from datetime import timedelta
from decimal import Decimal, InvalidOperation
import random
from functools import wraps
from core.models import Client, Product, Service, Quote, QuoteItem, Invoice, InvoiceItem

def tenant_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role == 'SYSTEM_ADMIN' or request.user.is_superuser:
            return redirect('admin_dashboard')
        if not getattr(request.user, 'company_id', None):
            from django.contrib.auth import logout
            logout(request)
            messages.error(request, "Session invalide")
            return redirect('accueil')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def parse_decimal(val, default='0'):
    try:
        d = Decimal(str(val))
        if d < 0: return Decimal(default)
        if d > Decimal('1000000000'): return Decimal(default)
        return d
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)

# ===== DASHBOARD - CORRIGÉ ICI =====
@tenant_required
def dashboard(request):
    company = request.user.company
    total_clients = Client.objects.filter(company=company).count()
    
    # On sécurise la lecture des factures
    try:
        recent_invoices = list(Invoice.objects.filter(company=company).order_by('-created_at')[:5])
        # On nettoie les montants invalides à la volée
        for inv in recent_invoices:
            try:
                float(inv.total_amount)
            except:
                inv.total_amount = 0
    except Exception as e:
        print(f"Erreur recent_invoices: {e}")
        recent_invoices = []

    total_revenue = 0
    pending_invoices = 0
    try:
        pending_invoices = Invoice.objects.filter(company=company, status='sent').count()
        # On calcule sans utiliser Sum qui plante sur Decimal invalide
        for inv in Invoice.objects.filter(company=company, status='paid'):
            try:
                total_revenue += float(inv.total_amount or 0)
            except:
                pass
    except:
        pass

    return render(request, 'tenant/dashboard.html', {
        'total_clients': total_clients,
        'recent_invoices': recent_invoices,
        'total_revenue': total_revenue,
        'pending_invoices': pending_invoices,
    })
# ===== CLIENTS =====
@tenant_required
def clients_list(request):
    clients = Client.objects.filter(company=request.user.company).order_by('-created_at')
    return render(request, 'tenant/clients/list.html', {'clients': clients})

@tenant_required
@require_http_methods(["GET", "POST"])
def client_add(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()[:100]
        last_name = request.POST.get('last_name', '').strip()[:100]
        email = request.POST.get('email', '').strip()[:255]
        phone = request.POST.get('phone', '').strip()[:20]
        if not first_name or not last_name:
            messages.error(request, "Prénom et Nom obligatoires.")
            return render(request, 'tenant/clients/add_edit.html')
        Client.objects.create(company=request.user.company, first_name=first_name, last_name=last_name, email=email, phone=phone, address=request.POST.get('address','').strip()[:1000], city=request.POST.get('city','').strip()[:100], postal_code=request.POST.get('postal_code','').strip()[:20], country=request.POST.get('country','').strip()[:100])
        messages.success(request, "Client ajouté.")
        return redirect('clients_list')
    return render(request, 'tenant/clients/add_edit.html')

@tenant_required
@require_http_methods(["GET", "POST"])
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk, company=request.user.company)
    if request.method == 'POST':
        client.first_name = request.POST.get('first_name', '').strip()[:100]
        client.last_name = request.POST.get('last_name', '').strip()[:100]
        client.email = request.POST.get('email', '').strip()[:255]
        client.phone = request.POST.get('phone', '').strip()[:20]
        client.address = request.POST.get('address', '').strip()[:1000]
        if not client.first_name or not client.last_name:
            messages.error(request, "Prénom et Nom obligatoires.")
            return render(request, 'tenant/clients/add_edit.html', {'client': client})
        client.save()
        messages.success(request, "Client mis à jour.")
        return redirect('clients_list')
    return render(request, 'tenant/clients/add_edit.html', {'client': client})

@tenant_required
@require_http_methods(["POST"])
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk, company=request.user.company)
    client.delete()
    messages.success(request, "Client supprimé.")
    return redirect('clients_list')

# ===== PRODUCTS =====
@tenant_required
def products_list(request):
    products = Product.objects.filter(company=request.user.company).order_by('-created_at')
    return render(request, 'tenant/products/list.html', {'products': products})

@tenant_required
@require_http_methods(["GET", "POST"])
def product_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()[:255]
        if not name:
            messages.error(request, "Nom requis.")
            return render(request, 'tenant/products/add_edit.html')
        Product.objects.create(company=request.user.company, name=name, description=request.POST.get('description','').strip()[:2000], price=parse_decimal(request.POST.get('price','0')), tax_rate=parse_decimal(request.POST.get('tax_rate','0')), unit=request.POST.get('unit','pièce')[:50], stock_quantity=int(parse_decimal(request.POST.get('stock_quantity','0'))))
        messages.success(request, "Produit ajouté.")
        return redirect('products_list')
    return render(request, 'tenant/products/add_edit.html')

@tenant_required
@require_http_methods(["GET", "POST"])
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    if request.method == 'POST':
        product.name = request.POST.get('name', '').strip()[:255]
        product.price = parse_decimal(request.POST.get('price','0'))
        product.tax_rate = parse_decimal(request.POST.get('tax_rate','0'))
        product.save()
        messages.success(request, "Produit mis à jour.")
        return redirect('products_list')
    return render(request, 'tenant/products/add_edit.html', {'product': product})

@tenant_required
@require_http_methods(["POST"])
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    product.delete()
    messages.success(request, "Produit supprimé.")
    return redirect('products_list')

# ===== SERVICES =====
@tenant_required
def services_list(request):
    services = Service.objects.filter(company=request.user.company).order_by('-created_at')
    return render(request, 'tenant/services/list.html', {'services': services})

@tenant_required
@require_http_methods(["GET", "POST"])
def service_add(request):
    if request.method == 'POST':
        Service.objects.create(company=request.user.company, name=request.POST.get('name','').strip()[:255], description=request.POST.get('description','').strip()[:2000], price=parse_decimal(request.POST.get('price','0')), tax_rate=parse_decimal(request.POST.get('tax_rate','0')))
        messages.success(request, "Service ajouté.")
        return redirect('services_list')
    return render(request, 'tenant/services/add_edit.html')

@tenant_required
@require_http_methods(["GET", "POST"])
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk, company=request.user.company)
    if request.method == 'POST':
        service.name = request.POST.get('name','').strip()[:255]
        service.price = parse_decimal(request.POST.get('price','0'))
        service.save()
        messages.success(request, "Service mis à jour.")
        return redirect('services_list')
    return render(request, 'tenant/services/add_edit.html', {'service': service})

@tenant_required
@require_http_methods(["POST"])
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk, company=request.user.company)
    service.delete()
    messages.success(request, "Service supprimé.")
    return redirect('services_list')

def extract_items_from_post(post_data):
    items = []
    for index in range(50):
        desc = post_data.get(f'items[{index}][description]', '').strip()[:1000]
        if not desc: continue
        qty = parse_decimal(post_data.get(f'items[{index}][quantity]', '1'))
        price = parse_decimal(post_data.get(f'items[{index}][unit_price]', '0'))
        tax = parse_decimal(post_data.get(f'items[{index}][tax_rate]', '19.25'))
        if qty <= 0: qty = Decimal('1')
        items.append({'description': desc, 'quantity': qty, 'unit_price': price, 'tax_rate': tax})
    return items

@tenant_required
def quotes_list(request):
    quotes = Quote.objects.filter(company=request.user.company).order_by('-created_at')
    return render(request, 'tenant/quotes/list.html', {'quotes': quotes})

@tenant_required
@require_http_methods(["GET", "POST"])
def quote_add(request):
    company = request.user.company
    clients = Client.objects.filter(company=company)
    if request.method == 'POST':
        client = get_object_or_404(Client, id=request.POST.get('client_id'), company=company)
        items = extract_items_from_post(request.POST)
        if not items:
            messages.error(request, "Au moins un article requis.")
            return render(request, 'tenant/quotes/add_edit.html', {'clients': clients})
        with transaction.atomic():
            quote_num = f"DEV-{timezone.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            total = sum((i['quantity'] * i['unit_price']) * (1 + i['tax_rate']/100) for i in items)
            tax = sum((i['quantity'] * i['unit_price']) * (i['tax_rate']/100) for i in items)
            quote = Quote.objects.create(company=company, client=client, quote_number=quote_num, issue_date=request.POST.get('issue_date'), expiry_date=request.POST.get('expiry_date'), status=request.POST.get('status','draft'), notes=request.POST.get('notes','')[:2000], total_amount=total, tax_amount=tax)
            for item in items:
                QuoteItem.objects.create(quote=quote, item_type='product', description=item['description'], quantity=item['quantity'], unit_price=item['unit_price'], tax_rate=item['tax_rate'], total_price=(item['quantity'] * item['unit_price']) * (1 + item['tax_rate']/100))
        messages.success(request, f"Devis {quote.quote_number} créé.")
        return redirect('quotes_list')
    today = timezone.now().date()
    return render(request, 'tenant/quotes/add_edit.html', {'clients': clients, 'today': today, 'expiry': today + timedelta(days=30)})

@tenant_required
def quote_detail(request, pk):
    quote = get_object_or_404(Quote, pk=pk, company=request.user.company)
    return render(request, 'tenant/quotes/detail.html', {'quote': quote})

@tenant_required
def quote_pdf(request, pk):
    quote = get_object_or_404(Quote, pk=pk, company=request.user.company)
    return render(request, 'tenant/quotes/pdf_print.html', {'quote': quote, 'company': request.user.company})

@tenant_required
@require_http_methods(["POST"])
def quote_delete(request, pk):
    quote = get_object_or_404(Quote, pk=pk, company=request.user.company)
    quote.delete()
    messages.success(request, "Devis supprimé.")
    return redirect('quotes_list')

@tenant_required
@require_http_methods(["POST"])
def quote_to_invoice(request, pk):
    quote = get_object_or_404(Quote, pk=pk, company=request.user.company)
    with transaction.atomic():
        inv_num = f"FAC-{timezone.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        today = timezone.now().date()
        invoice = Invoice.objects.create(company=quote.company, client=quote.client, invoice_number=inv_num, issue_date=today, due_date=today+timedelta(days=30), status='draft', total_amount=quote.total_amount, tax_amount=quote.tax_amount, notes=f"Depuis {quote.quote_number}")
        for item in quote.items.all():
            InvoiceItem.objects.create(invoice=invoice, item_type=item.item_type, description=item.description, quantity=item.quantity, unit_price=item.unit_price, tax_rate=item.tax_rate, total_price=item.total_price)
        quote.status = 'invoiced'
        quote.save()
    messages.success(request, f"Facture {invoice.invoice_number} générée.")
    return redirect('invoices_list')

@tenant_required
def invoices_list(request):
    invoices = Invoice.objects.filter(company=request.user.company).order_by('-created_at')
    return render(request, 'tenant/invoices/list.html', {'invoices': invoices})

@tenant_required
@require_http_methods(["GET", "POST"])
def invoice_add(request):
    company = request.user.company
    clients = Client.objects.filter(company=company)
    if request.method == 'POST':
        client = get_object_or_404(Client, id=request.POST.get('client_id'), company=company)
        items = extract_items_from_post(request.POST)
        if not items:
            messages.error(request, "Au moins un article requis.")
            return render(request, 'tenant/invoices/add_edit.html', {'clients': clients})
        with transaction.atomic():
            inv_num = f"FAC-{timezone.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            total = sum((i['quantity'] * i['unit_price']) * (1 + i['tax_rate']/100) for i in items)
            tax = sum((i['quantity'] * i['unit_price']) * (i['tax_rate']/100) for i in items)
            invoice = Invoice.objects.create(company=company, client=client, invoice_number=inv_num, issue_date=request.POST.get('issue_date'), due_date=request.POST.get('due_date'), status=request.POST.get('status','draft'), notes=request.POST.get('notes','')[:2000], total_amount=total, tax_amount=tax)
            for item in items:
                InvoiceItem.objects.create(invoice=invoice, item_type='product', description=item['description'], quantity=item['quantity'], unit_price=item['unit_price'], tax_rate=item['tax_rate'], total_price=(item['quantity'] * item['unit_price']) * (1 + item['tax_rate']/100))
        messages.success(request, f"Facture {invoice.invoice_number} créée.")
        return redirect('invoices_list')
    today = timezone.now().date()
    return render(request, 'tenant/invoices/add_edit.html', {'clients': clients, 'today': today, 'due': today+timedelta(days=30)})

@tenant_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, company=request.user.company)
    return render(request, 'tenant/invoices/detail.html', {'invoice': invoice})

@tenant_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, company=request.user.company)
    return render(request, 'tenant/invoices/pdf_print.html', {'invoice': invoice, 'company': request.user.company})

@tenant_required
@require_http_methods(["POST"])
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, company=request.user.company)
    invoice.delete()
    messages.success(request, "Facture supprimée.")
    return redirect('invoices_list')

@tenant_required
@require_http_methods(["GET", "POST"])
def settings_view(request):
    company = request.user.company
    if request.method == 'POST':
        company.name = request.POST.get('name','').strip()[:255]
        company.address = request.POST.get('address','').strip()[:1000]
        company.city = request.POST.get('city','').strip()[:100]
        company.phone = request.POST.get('phone','').strip()[:20]
        if 'logo' in request.FILES:
            company.logo = request.FILES['logo']
        if not company.name:
            messages.error(request, "Nom obligatoire.")
            return render(request, 'tenant/settings.html', {'company': company})
        company.save()
        messages.success(request, "Paramètres mis à jour.")
        return redirect('settings')
    return render(request, 'tenant/settings.html', {'company': company})