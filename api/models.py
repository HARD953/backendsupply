from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from rest_framework.exceptions import ValidationError

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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user')
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
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
    # id = models.CharField(max_length=50, primary_key=True)
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
    # id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=100, blank=True, null=True)
    permissions = models.ManyToManyField(Permission, related_name='roles')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Rôle"
        verbose_name_plural = "Rôles"


def today_date():
    return timezone.now().date()

class UserProfile(models.Model):
    """
    Modèle pour étendre le modèle User de Django avec des informations supplémentaires.
    """
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('suspended', 'Suspendu'),
    ]
    owner = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='managed_profiles',
        verbose_name="Propriétaire/Créateur"
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='users')
    join_date = models.DateField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    points_of_sale = models.ManyToManyField(PointOfSale, related_name='users', blank=True)

    # Informations directes de l'établissement
    establishment_name = models.CharField(
        max_length=200, 
        verbose_name="Nom de l'établissement"
    )
    establishment_phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="Téléphone établissement"
    )
    establishment_email = models.EmailField(
        blank=True, 
        null=True, 
        verbose_name="Email établissement"
    )
    establishment_address = models.TextField(
        verbose_name="Adresse établissement"
    )
    establishment_type = models.CharField(
        max_length=50, 
        verbose_name="Type d'établissement"
    )
    establishment_registration_date = models.DateField(
        verbose_name="Date d'enregistrement",
        default=today_date
    )

    def __str__(self):
        return f"{self.user.username} - {self.establishment_name}"

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"

    def save(self, *args, **kwargs):
        """Méthode pour synchroniser éventuellement avec un POS existant"""
        super().save(*args, **kwargs)
        
        # # Si on veut créer automatiquement un POS à partir des infos
        # if not self.points_of_sale.exists() and self.establishment_name:
        #     pos = PointOfSale.objects.create(
        #         name=self.establishment_name,
        #         phone=self.establishment_phone,
        #         email=self.establishment_email,
        #         address=self.establishment_address,
        #         type=self.establishment_type,
        #         registration_date=self.establishment_registration_date,
        #         user=self.user,  # Add this line to set the user relationship
        #     )
        #     self.points_of_sale.add(pos)
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

    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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

    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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

    customer = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name="Client"
    )
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
        return f"Commande {self.id} - {self.customer.user}"

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
    quantity_affecte = models.PositiveIntegerField(default=0)
    
    def save(self, *args, **kwargs):
        # Calcul du total
        self.total = self.quantity * self.price
        
        # Vérifier que quantity_affecte ne dépasse jamais quantity
        if self.quantity_affecte > self.quantity:
            raise ValidationError("La quantité affectée ne peut pas dépasser la quantité commandée")
        
        # Si c'est une nouvelle instance (création)
        if self.pk is None:
            # Décrémenter le stock de la variante
            if self.product_variant:
                self.product_variant.current_stock -= self.quantity
                self.product_variant.save()
        else:
            # Si c'est une mise à jour, gérer la différence de quantité
            old_item = OrderItem.objects.get(pk=self.pk)
            if old_item.quantity != self.quantity and self.product_variant:
                quantity_diff = old_item.quantity - self.quantity
                self.product_variant.current_stock += quantity_diff
                self.product_variant.save()
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Restaurer le stock lors de la suppression
        if self.product_variant:
            self.product_variant.current_stock += self.quantity
            self.product_variant.save()
        super().delete(*args, **kwargs)

    def affecter_quantite(self, quantite):
        """
        Méthode pour affecter une quantité à cet article
        """
        if self.quantity_affecte + quantite > self.quantity:
            raise ValidationError(
                f"Impossible d'affecter {quantite} unités. "
                f"Quantité restante: {self.quantity - self.quantity_affecte}"
            )
        
        self.quantity_affecte += quantite
        self.save()
        
    def quantite_restante(self):
        """
        Retourne la quantité restante à affecter
        """
        return self.quantity - self.quantity_affecte
    
    def est_completement_affecte(self):
        """
        Vérifie si toute la quantité a été affectée
        """
        return self.quantity_affecte == self.quantity

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

    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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

    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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

    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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


from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class MobileVendor(models.Model):
    """
    Modèle pour les vendeurs ambulants liés aux points de vente
    """
    STATUS_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('en_conge', 'En congé'),
        ('suspendu', 'Suspendu'),
    ]
    
    VEHICLE_CHOICES = [
        ('moto', 'Moto'),
        ('tricycle', 'Tricycle'),
        ('velo', 'Vélo'),
        ('pied', 'À pied'),
        ('autre', 'Autre'),
    ]

    # # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # owner = models.ForeignKey(
    #     User, 
    #     on_delete=models.SET_NULL, 
    #     null=True, 
    #     related_name='managed_profiles',
    #     verbose_name="Propriétaire/Créateur"
    # )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mobile_vendor', null=True, blank=True)
    point_of_sale = models.ForeignKey(
        'PointOfSale', 
        on_delete=models.CASCADE, 
        related_name='mobile_vendors',
        verbose_name="Point de vente associé"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    photo = models.ImageField(upload_to='mobile_vendors/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='actif')
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_CHOICES, default='moto')
    vehicle_id = models.CharField(max_length=50, blank=True, null=True)
    zones = models.JSONField(default=list)  # Zones de vente sous forme de liste
    performance = models.FloatField(default=0.0)  # Performance en pourcentage
    average_daily_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date_joined = models.DateField(default=timezone.now)
    last_activity = models.DateTimeField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Vendeur ambulant"
        verbose_name_plural = "Vendeurs ambulants"
        ordering = ['-created_at']
        unique_together = ['first_name', 'last_name', 'point_of_sale']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.point_of_sale.name})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def update_performance(self):
        """Méthode pour calculer et mettre à jour la performance du vendeur"""
        # Implémentez votre logique de calcul de performance ici
        # Par exemple, basée sur les ventes récentes, l'assiduité, etc.
        pass

    def calculate_performance(self, start_date=None, end_date=None):
        """
        Calcule la performance du vendeur : 
        (ventes du vendeur / ventes totales de tous les vendeurs) * 100
        """
        # Filtrer par période si spécifiée
        vendor_filters = {'vendor': self}
        total_filters = {}
        
        if start_date:
            vendor_filters['created_at__gte'] = start_date
            total_filters['created_at__gte'] = start_date
        if end_date:
            vendor_filters['created_at__lte'] = end_date
            total_filters['created_at__lte'] = end_date
        
        # Ventes du vendeur spécifique
        vendor_sales = Sale.objects.filter(**vendor_filters).aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0
        
        # Ventes totales de TOUS les vendeurs
        total_sales = Sale.objects.filter(**total_filters).aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0
        
        # Éviter la division par zéro
        if total_sales == 0:
            return 0.0
        
        # Calcul du pourcentage
        performance = (vendor_sales / total_sales) * 100
        return round(performance, 2)
    
    def update_performance(self, start_date=None, end_date=None):
        """
        Met à jour la performance du vendeur
        """
        self.performance = self.calculate_performance(start_date, end_date)
        self.save(update_fields=['performance'])
    
    def get_recent_performance(self, days=30):
        """
        Performance sur les derniers jours
        """
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=days)
        return self.calculate_performance(start_date, end_date)

# models.py
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

class VendorActivity(models.Model):
    """
    Modèle pour suivre les activités quotidiennes des vendeurs ambulants
    """
    ACTIVITY_TYPES = [
        ('check_in', 'Check-in'),
        ('check_out', 'Check-out'),
        ('sale', 'Vente'),
        ('stock_replenishment', 'Réapprovisionnement'),
        ('incident', 'Incident'),
        ('other', 'Autre'),
    ]

    STATUS_CHOICES = [
        ('comptabilise', 'Comptabilise'),
        ('en_attente', 'En attente'),
    ]

    vendor = models.ForeignKey(
        'MobileVendor', 
        on_delete=models.CASCADE, 
        related_name='activities'
    )
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)
    location = models.JSONField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    related_order = models.ForeignKey(
        'Order', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='vendor_activities'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    quantity_assignes = models.PositiveIntegerField(default=0)
    quantity_restante = models.PositiveIntegerField(default=0)
    quantity_sales = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    class Meta:
        verbose_name = "Activité de vendeur"
        verbose_name_plural = "Activités des vendeurs"
        ordering = ['-timestamp']

    def clean(self):
        """Validation des données avant sauvegarde"""
        super().clean()
        
        # Si c'est un réapprovisionnement, s'assurer que quantity_restante est initialisée
        if (self.activity_type == 'stock_replenishment' and 
            self.quantity_assignes > 0 and 
            self.quantity_restante == 0):
            self.quantity_restante = self.quantity_assignes
        
        # Validation : quantity_restante ne peut pas être > quantity_assignes
        if self.quantity_restante > self.quantity_assignes:
            raise ValidationError("La quantité restante ne peut pas dépasser la quantité assignée")
        
        # Validation : quantity_sales + quantity_restante <= quantity_assignes
        # CORRECTION: Cette validation ne doit pas s'appliquer lors des mises à jour partielles
        total = self.quantity_sales + self.quantity_restante
        if total > self.quantity_assignes:
            # Tolérance pour les arrondis ou mise à jour en cours
            if total - self.quantity_assignes > 1:  # Tolérance de 1 unité
                raise ValidationError(
                    f"Incohérence : ventes ({self.quantity_sales}) + "
                    f"restantes ({self.quantity_restante}) > "
                    f"assignées ({self.quantity_assignes})"
                )

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour gérer l'affectation automatique
        """
        # CORRECTION: Initialiser quantity_restante pour TOUTES les activités, pas seulement les réapprovisionnements
        if self.quantity_restante == 0 and self.quantity_assignes > 0:
            self.quantity_restante = self.quantity_assignes
            print(f"🔧 Initialisation quantity_restante: {self.quantity_restante}")
        
        # Validation avant sauvegarde
        self.clean()
        
        # Si c'est une NOUVELLE activité de réapprovisionnement avec commande
        if (self._state.adding and 
            self.activity_type == 'stock_replenishment' and 
            self.quantity_assignes > 0 and
            self.related_order):
            
            print(f"🔧 Création activité réapprovisionnement - Quantité: {self.quantity_assignes}")
            
            # Sauvegarder d'abord pour avoir un ID
            super().save(*args, **kwargs)
            
            # Ensuite affecter la quantité aux articles
            try:
                self.affecter_quantite_commande()
            except ValidationError as e:
                print(f"❌ Erreur lors de l'affectation: {e}")
                # En cas d'erreur, supprimer l'instance créée
                self.delete()
                raise e
                
        else:
            # Pour les autres cas (mise à jour ou autres types)
            super().save(*args, **kwargs)

    def affecter_quantite_commande(self):
        """
        Affecte la quantité assignée aux articles de la commande
        """
        if not self.related_order:
            print("❌ Aucune commande liée")
            return
            
        print(f"🔧 Début affectation - Quantité à affecter: {self.quantity_assignes}")
        
        order_items = self.related_order.items.all()
        if not order_items.exists():
            print("❌ Aucun article dans la commande")
            return
            
        quantite_restante_apres_affectation = self.quantity_assignes
        
        for item in order_items:
            if quantite_restante_apres_affectation <= 0:
                break
                
            # Vérifier si l'article a besoin d'être affecté
            quantite_restante_item = item.quantite_restante()
            if quantite_restante_item > 0:
                quantite_a_affecter = min(quantite_restante_apres_affectation, quantite_restante_item)
                
                print(f"   Article {item.id}: {quantite_a_affecter} unités sur {quantite_restante_item} restantes")
                
                try:
                    # Affecter la quantité à l'article
                    item.affecter_quantite(quantite_a_affecter)
                    quantite_restante_apres_affectation -= quantite_a_affecter
                    print(f"   ✅ Affecté: {quantite_a_affecter}, Reste: {quantite_restante_apres_affectation}")
                except ValidationError as e:
                    print(f"   ❌ Erreur d'affectation pour l'article {item.id}: {e}")
                    continue
        
        # Mettre à jour la quantité restante
        self.quantity_restante = quantite_restante_apres_affectation
        print(f"🔧 Quantité restante après affectation: {self.quantity_restante}")
        
        # Sauvegarder la quantité restante mise à jour
        super().save(update_fields=['quantity_restante'])
        
        if quantite_restante_apres_affectation > 0:
            error_msg = f"{quantite_restante_apres_affectation} unités n'ont pas pu être affectées"
            print(f"   ⚠️ {error_msg}")

    def peut_vendre(self, quantite_demandee):
        """Vérifie si la quantité demandée peut être vendue"""
        return quantite_demandee <= self.quantity_restante
    
    @transaction.atomic
    def vendre_avec_verrouillage(self, quantite):
        """
        Effectue une vente avec verrouillage atomique
        Cette méthode garantit la cohérence des données lors des ventes simultanées
        """
        if quantite <= 0:
            raise ValidationError("La quantité de vente doit être positive")
        
        # Verrouiller l'instance en base pour éviter les conditions de concurrence
        # select_for_update() verrouille la ligne jusqu'à la fin de la transaction
        locked_activity = VendorActivity.objects.select_for_update().get(id=self.id)
        
        print(f"🔒 Verrouillage activité {locked_activity.id}")
        print(f"   Quantité demandée: {quantite}")
        print(f"   Quantité restante actuelle: {locked_activity.quantity_restante}")
        print(f"   Quantité assignée: {locked_activity.quantity_assignes}")
        
        # CORRECTION: Vérifier et corriger l'initialisation si nécessaire
        if locked_activity.quantity_restante == 0 and locked_activity.quantity_assignes > 0 and locked_activity.quantity_sales == 0:
            print(f"🔧 Correction: initialisation quantity_restante à {locked_activity.quantity_assignes}")
            locked_activity.quantity_restante = locked_activity.quantity_assignes
            # Mise à jour immédiate en base
            VendorActivity.objects.filter(id=locked_activity.id).update(
                quantity_restante=locked_activity.quantity_assignes
            )
        
        # Vérification avec les données verrouillées (les plus récentes)
        if quantite > locked_activity.quantity_restante:
            raise ValidationError(
                f"Impossible de vendre {quantite} unités. "
                f"Quantité restante: {locked_activity.quantity_restante}"
            )
        
        # Mise à jour atomique
        locked_activity.quantity_sales += quantite
        locked_activity.quantity_restante -= quantite
        
        # CORRECTION: Utiliser une mise à jour directe en base pour éviter clean()
        VendorActivity.objects.filter(id=locked_activity.id).update(
            quantity_sales=locked_activity.quantity_sales,
            quantity_restante=locked_activity.quantity_restante
        )
        
        print(f"✅ Vente effectuée:")
        print(f"   Nouvelles ventes totales: {locked_activity.quantity_sales}")
        print(f"   Nouvelle quantité restante: {locked_activity.quantity_restante}")
        print(f"🔓 Déverrouillage activité {locked_activity.id}")
        
        # Mettre à jour l'instance actuelle avec les nouvelles valeurs
        self.quantity_sales = locked_activity.quantity_sales
        self.quantity_restante = locked_activity.quantity_restante
        
        return locked_activity
    
    def incrementer_ventes(self, quantite):
        """
        ANCIENNE MÉTHODE - DÉPRÉCIÉE
        Cette méthode n'est plus utilisée car elle ne gère pas les conditions de concurrence
        """
        print("⚠️ ATTENTION: incrementer_ventes() est déprécié. Utilisez vendre_avec_verrouillage()")
        
        if quantite <= 0:
            return
            
        # Vérification de sécurité
        if quantite > self.quantity_restante:
            raise ValidationError(
                f"Impossible d'incrémenter les ventes de {quantite}. "
                f"Quantité restante: {self.quantity_restante}"
            )
        
        self.quantity_sales += quantite
        self.quantity_restante -= quantite
        
        # Sauvegarder avec validation
        self.save(update_fields=['quantity_sales', 'quantity_restante'])
        print(f"📊 Ventes incrémentées: +{quantite}, Restant: {self.quantity_restante}")
    
    def quantite_restante_calculee(self):
        """Retourne la quantité restante calculée (pour vérification)"""
        return max(0, self.quantity_assignes - self.quantity_sales)
    
    def est_completement_vendu(self):
        """Vérifie si tout le stock a été vendu"""
        return self.quantity_restante <= 0
    
    def verifier_coherence(self):
        """Vérifie la cohérence des quantités"""
        calculee = self.quantite_restante_calculee()
        if calculee != self.quantity_restante:
            print(f"⚠️ Incohérence détectée:")
            print(f"   Quantité restante stockée: {self.quantity_restante}")
            print(f"   Quantité restante calculée: {calculee}")
            return False
        return True
    
    def corriger_quantite_restante(self):
        """Corrige la quantité restante en cas d'incohérence"""
        ancienne_valeur = self.quantity_restante
        
        # Si quantity_restante est 0 mais qu'il devrait y avoir du stock
        if (self.quantity_restante == 0 and 
            self.quantity_assignes > 0 and 
            self.quantity_sales == 0):
            # Cas spécial : initialisation manquée
            self.quantity_restante = self.quantity_assignes
            print(f"🔧 Initialisation manquée corrigée: 0 → {self.quantity_restante}")
        else:
            # Cas normal : recalcul basé sur les ventes
            self.quantity_restante = self.quantite_restante_calculee()
        
        if ancienne_valeur != self.quantity_restante:
            self.save(update_fields=['quantity_restante'])
            print(f"🔧 Quantité restante corrigée: {ancienne_valeur} → {self.quantity_restante}")
        
        return self.quantity_restante

    def __str__(self):
        order_id = self.related_order.id if self.related_order else "Aucune commande"
        return f"{self.vendor.full_name} - {order_id} - {self.get_activity_type_display()} - {self.created_at.date()}"


class Sale(models.Model):
    """
    Modèle pour enregistrer les ventes
    """
    vendor_activity = models.ForeignKey(
        'VendorActivity', 
        on_delete=models.CASCADE,
        related_name='sales'
    )
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Vente"
        verbose_name_plural = "Ventes"
        ordering = ['-timestamp']
    
    def clean(self):
        """Validation avant sauvegarde"""
        super().clean()
        
        if self.quantity <= 0:
            raise ValidationError("La quantité doit être positive")
        
        if not self.vendor_activity:
            raise ValidationError("Une activité de vendeur est requise")
    
    def save(self, *args, **kwargs):
        """
        Surcharge de save() pour gérer automatiquement les ventes
        """
        # Validation
        self.clean()
        
        # Si c'est une nouvelle vente
        if self._state.adding:
            print(f"💰 Création nouvelle vente: {self.quantity} unités")
            
            # Utiliser la méthode atomique pour effectuer la vente
            try:
                self.vendor_activity.vendre_avec_verrouillage(self.quantity)
                print(f"✅ Stock mis à jour avec succès")
            except ValidationError as e:
                print(f"❌ Erreur lors de la vente: {e}")
                raise e
        
        # Sauvegarder la vente
        super().save(*args, **kwargs)
        print(f"💾 Vente sauvegardée: ID={self.id}")
    
    def __str__(self):
        return f"Vente {self.quantity} unités - {self.vendor_activity.vendor.full_name} - {self.created_at.date()}"
    
class VendorPerformance(models.Model):
    """
    Modèle pour enregistrer les performances mensuelles des vendeurs
    """
    vendor = models.ForeignKey(
        MobileVendor, 
        on_delete=models.CASCADE, 
        related_name='performances'
    )
    month = models.DateField()  # Premier jour du mois
    total_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    orders_completed = models.PositiveIntegerField(default=0)
    days_worked = models.PositiveIntegerField(default=0)
    distance_covered = models.FloatField(default=0.0)  # En kilomètres
    performance_score = models.FloatField(default=0.0)
    bonus_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Performance de vendeur"
        verbose_name_plural = "Performances des vendeurs"
        unique_together = ['vendor', 'month']
        ordering = ['-month']

    def __str__(self):
        return f"{self.vendor.full_name} - {self.month.strftime('%B %Y')}"

    def calculate_performance(self):
        """Méthode pour calculer le score de performance"""
        # Implémentez votre logique de calcul ici
        pass

class Purchase(models.Model):
    """
    Modèle pour représenter les achats effectués par les vendeurs ambulants
    """
    vendor = models.ForeignKey(
        'MobileVendor',
        on_delete=models.CASCADE,
        related_name='purchases',
        verbose_name="Vendeur ambulant"
    )
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    zone = models.CharField(max_length=100, verbose_name="Zone de vente")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant vendu")
    photo = models.ImageField(upload_to='purchases/', blank=True, null=True, verbose_name="Photo")
    purchase_date = models.DateTimeField(default=timezone.now, verbose_name="Date de l'achat")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")

    # ✅ Nouveaux attributs
    base = models.CharField(max_length=100, blank=True, verbose_name="Base")
    pushcard_type = models.CharField(max_length=100, blank=True, verbose_name="Type de pushcard")
    latitude = models.FloatField(blank=True, null=True, verbose_name="Latitude")
    longitude = models.FloatField(blank=True, null=True, verbose_name="Longitude")
    phone = models.CharField(max_length=100, blank=True, verbose_name="Type de pushcard")

    class Meta:
        verbose_name = "Achat"
        verbose_name_plural = "Achats"
        ordering = ['-purchase_date']

    def __str__(self):
        return f"Achat de {self.first_name} {self.last_name} - {self.amount} ({self.zone})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def update_performance(self):
        """Méthode pour calculer et mettre à jour la performance du vendeur"""
        purchases = self.purchases.all()
        total_sales = sum(purchase.amount for purchase in purchases)
        purchase_count = purchases.count()

        # Exemple de calcul : performance basée sur le montant total vendu
        if purchase_count > 0:
            self.performance = (total_sales / purchase_count) * 100
        else:
            self.performance = 0.0

        days_active = (timezone.now().date() - self.date_joined).days or 1
        self.average_daily_sales = total_sales / days_active

        self.save()

class Sale(models.Model):
    """
    Modèle pour enregistrer les ventes
    """
    product_variant = models.ForeignKey(
        'ProductVariant',
        on_delete=models.CASCADE,
        related_name='sales'
    )
    customer = models.ForeignKey(
        'Purchase',
        on_delete=models.CASCADE,
        related_name='purchases'
    )
    quantity = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    vendor = models.ForeignKey(
        'MobileVendor',
        on_delete=models.CASCADE,
        related_name='sales_vendors'
    )
    vendor_activity = models.ForeignKey(
        'VendorActivity', 
        on_delete=models.CASCADE,
        related_name='sales'
    )
    
    class Meta:
        db_table = 'sales'
        ordering = ['-created_at']
    
    def clean(self):
        """Validation avant sauvegarde"""
        super().clean()
        
        if self.quantity <= 0:
            raise ValidationError("La quantité doit être positive")
        
        if not self.vendor_activity:
            raise ValidationError("Une activité de vendeur est requise")
    
    def save(self, *args, **kwargs):
        """
        Surcharge de save() pour gérer automatiquement les ventes
        """
        # Validation
        self.clean()
        
        # Si c'est une nouvelle vente
        if self._state.adding:
            print(f"💰 Création nouvelle vente: {self.quantity} unités")
            
            # Utiliser la méthode atomique pour effectuer la vente
            try:
                self.vendor_activity.vendre_avec_verrouillage(self.quantity)
                print(f"✅ Stock mis à jour avec succès")
            except ValidationError as e:
                print(f"❌ Erreur lors de la vente: {e}")
                raise e
        
        # Sauvegarder la vente
        super().save(*args, **kwargs)
        print(f"💾 Vente sauvegardée: ID={self.id}")
    
    def __str__(self):
        return f"Vente {self.quantity} unités - {self.vendor_activity.vendor.full_name} - {self.timestamp.date()}"