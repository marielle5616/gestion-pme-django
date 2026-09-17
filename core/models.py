from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
import os

def validate_logo_size(image):
    max_size = 2 * 1024 * 1024  # 2Mo
    if image.size > max_size:
        raise ValidationError("Logo trop volumineux (max 2Mo)")

class Company(models.Model):
    PLAN_CHOICES = [('starter','Starter'),('business','Business'),('enterprise','Enterprise')]
    STATUS_CHOICES = [('active','Actif'),('inactive','Inactif'),('suspended','Suspendu')]
    
    name = models.CharField(max_length=255)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    website = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    plan = models.CharField(max_length=50, choices=PLAN_CHOICES, default='starter')
    subscription_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='inactive')
    created_at = models.DateTimeField(auto_now_add=True)
    logo = models.ImageField(
        upload_to='logos/', null=True, blank=True,
        validators=[
            FileExtensionValidator(['jpg','jpeg','png','webp']),
            validate_logo_size
        ]
    )
    def __str__(self): return self.name

class CustomUser(AbstractUser):
    ROLE_CHOICES = [('admin','Admin'),('user','User')]
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']
    def __str__(self): return self.email
    
    @property
    def tenant(self):
        return self.company

class Client(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='clients')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.first_name} {self.last_name}"

class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    unit = models.CharField(max_length=50, default='pièce')
    stock_quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class Service(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class Quote(models.Model):
    STATUS_CHOICES = [('draft','Brouillon'),('sent','Envoyé'),('accepted','Accepté'),('rejected','Refusé'),('invoiced','Facturé')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='quotes')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='quotes')
    quote_number = models.CharField(max_length=100, unique=True)
    issue_date = models.DateField()
    expiry_date = models.DateField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.quote_number

class QuoteItem(models.Model):
    TYPE_CHOICES = [('product','Produit'),('service','Service')]
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='items')
    item_id = models.IntegerField(null=True, blank=True)
    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self): return f"{self.item_type} - {self.description[:30]}"

class Invoice(models.Model):
    STATUS_CHOICES = [('draft','Brouillon'),('sent','Envoyé'),('paid','Payé'),('overdue','En retard')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=100, unique=True)
    issue_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.invoice_number

class InvoiceItem(models.Model):
    TYPE_CHOICES = [('product','Produit'),('service','Service')]
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    item_id = models.IntegerField(null=True, blank=True)
    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='product')
    description = models.TextField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self): return f"{self.item_type} - {self.description[:30]}"

class PasswordResetToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True) # unique=True ajouté
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.user.email} - {self.token[:10]}"
    
    def is_valid(self):
        from django.utils import timezone
        return not self.used and self.expires_at > timezone.now()