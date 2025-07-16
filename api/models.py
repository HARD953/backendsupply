from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Category(models.Model):
    """
    Modèle pour les catégories de produits (ex. Céréales, Huiles, Épicerie).
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

class Supplier(models.Model):
    """
    Modèle pour les fournisseurs (ex. Importateur Adjamé, Huilerie Locale).
    """
    name = models.CharField(max_length=200)
    types = models.CharField(max_length=200)
    contact = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    logo = models.ImageField(upload_to='suppliers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"

class PointOfSale(models.Model):
    """
    Modèle pour les points de vente (boutiques, supermarchés, grossistes, etc.).
    """
    TYPE_CHOICES = [
        ('boutique', 'Boutique'),
        ('supermarche', 'Supermarché'),
        ('superette', 'Supérette'),
        ('epicerie', 'Épicerie'),
        ('demi_grossiste', 'Demi-Grossiste'),
        ('grossiste', 'Grossiste'),
    ]

    STATUS_CHOICES = [
        ('actif', 'Actif'),
        ('suspendu', 'Suspendu'),
        ('en_attente', 'En attente'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200) 
    owner = models.CharField(max_length=200)  # Propriétaire
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    district = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    commune = models.CharField(max_length=100)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    registration_date = models.DateField()
    turnover = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    monthly_orders = models.PositiveIntegerField(default=0)
    evaluation_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.commune})"

    class Meta:
        verbose_name = "Point de vente"
        verbose_name_plural = "Points de vente"

class Permission(models.Model):
    """
    Modèle pour les permissions (ex. gestion des stocks, consultation des rapports).
    """
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.category})"

    class Meta:
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"

class Role(models.Model):
    """
    Modèle pour les rôles des utilisateurs (ex. Super Admin, Gestionnaire Stock).
    """
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=100, blank=True, null=True)
    permissions = models.ManyToManyField(Permission, related_name='roles')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Rôle"
        verbose_name_plural = "Rôles"

class UserProfile(models.Model):
    """
    Modèle pour étendre le modèle User de Django avec des informations supplémentaires.
    """
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('suspended', 'Suspendu'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='users')
    join_date = models.DateField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.role.name if self.role else 'No Role'})"

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"

class ProductFormat(models.Model):
    """
    Modèle pour les différents formats d'un produit (ex. 1kg, 500g, 250ml)
    """
    name = models.CharField(max_length=100)  # Ex: "1kg", "500g", "Pack de 6"
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Format de produit"
        verbose_name_plural = "Formats de produit"

class Product(models.Model):
    """
    Modèle pour les produits, correspondant à l'interface Product du frontend.
    """
    STATUS_CHOICES = [
        ('en_stock', 'En stock'),
        ('stock_faible', 'Stock faible'),
        ('rupture', 'Rupture'),
        ('surstockage', 'Surstockage'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    main_image = models.ImageField(upload_to='products/', blank=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='products')
    point_of_sale = models.ForeignKey(PointOfSale, on_delete=models.CASCADE, related_name='products')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_stock')
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"

class ProductVariant(models.Model):
    """
    Modèle pour les variantes de produits (différents formats avec leurs propres stocks et prix)
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    format = models.ForeignKey(ProductFormat, on_delete=models.SET_NULL, null=True, blank=True)
    current_stock = models.PositiveIntegerField(default=0)
    min_stock = models.PositiveIntegerField(default=0)
    max_stock = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    barcode = models.CharField(max_length=50, blank=True, null=True, unique=True)
    image = models.ImageField(upload_to='product_variants/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # Mise à jour automatique du statut du produit parent
        product = self.product
        if self.current_stock == 0:
            product.status = 'rupture'
        elif self.current_stock <= self.min_stock:
            product.status = 'stock_faible'
        elif self.current_stock > self.max_stock:
            product.status = 'surstockage'
        else:
            product.status = 'en_stock'
        product.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.format.name if self.format else 'Sans format'}"

    class Meta:
        verbose_name = "Variante de produit"
        verbose_name_plural = "Variantes de produit"

class ProductImage(models.Model):
    """
    Modèle pour les images supplémentaires des produits
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    caption = models.CharField(max_length=200, blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "Image de produit"
        verbose_name_plural = "Images de produit"

    def __str__(self):
        return f"Image pour {self.product.name}"

class StockMovement(models.Model):
    """
    Modèle pour les mouvements de stock, correspondant à l'interface StockMovement du frontend.
    """
    MOVEMENT_TYPES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
        ('ajustement', 'Ajustement'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='movements')
    type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.PositiveIntegerField()
    date = models.DateTimeField(default=timezone.now)
    reason = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stock_movements')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        variant = self.product_variant
        if self.type == 'entree':
            variant.current_stock += self.quantity
        elif self.type == 'sortie':
            variant.current_stock = max(0, variant.current_stock - self.quantity)
        elif self.type == 'ajustement':
            variant.current_stock = self.quantity
        variant.save()

    def __str__(self):
        return f"{self.type} - {self.product_variant.product.name} ({self.quantity})"

    class Meta:
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"

class Order(models.Model):
    """
    Modèle pour les commandes, correspondant aux données du frontend.
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('shipped', 'Expédiée'),
        ('delivered', 'Livrée'),
        ('cancelled', 'Annulée'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
    ]

    id = models.CharField(max_length=20, primary_key=True)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    customer_address = models.TextField()
    point_of_sale = models.ForeignKey(PointOfSale, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    delivery_date = models.DateField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Commande {self.id} - {self.customer_name}"

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"

class OrderItem(models.Model):
    """
    Modèle pour les articles d'une commande.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, related_name='order_items')
    name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (x{self.quantity})"

    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"

class Dispute(models.Model):
    """
    Modèle pour les contentieux/litiges entre acteurs (entreprises, distributeurs, particuliers).
    """
    STATUS_CHOICES = [
        ('en_cours', 'En cours'),
        ('resolu', 'Résolu'),
        ('en_attente', 'En attente'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='disputes', null=True, blank=True)
    complainant = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='disputes_filed')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    resolution_details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Contentieux {self.id} - {self.order.id if self.order else 'Sans commande'}"

    class Meta:
        verbose_name = "Contentieux"
        verbose_name_plural = "Contentieux"

class Token(models.Model):
    """
    Modèle pour les jetons utilisés dans les transactions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tokens')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Portefeuille {self.user.username} - {self.balance}"

    class Meta:
        verbose_name = "Jeton"
        verbose_name_plural = "Jetons"

class TokenTransaction(models.Model):
    """
    Modèle pour les transactions de jetons (recharge, paiement, etc.).
    """
    TYPE_CHOICES = [
        ('recharge', 'Recharge'),
        ('payment', 'Paiement'),
        ('refund', 'Remboursement'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.ForeignKey(Token, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='token_transactions')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        token = self.token
        if self.type == 'recharge':
            token.balance += self.amount
        elif self.type in ['payment', 'refund']:
            token.balance = max(0, token.balance - self.amount)
        token.save()

    def __str__(self):
        return f"{self.type} - {self.amount} pour {self.token.user.username}"

    class Meta:
        verbose_name = "Transaction de jeton"
        verbose_name_plural = "Transactions de jetons"

class Notification(models.Model):
    """
    Modèle pour les notifications automatiques (commandes, stocks, promotions).
    """
    TYPE_CHOICES = [
        ('stock_alert', 'Alerte de stock'),
        ('order_update', 'Mise à jour commande'),
        ('promotion', 'Promotion'),
        ('dispute', 'Contentieux'),
        ('general', 'Général'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.user.username}"

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"