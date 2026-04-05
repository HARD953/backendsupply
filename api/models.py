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

# models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class Agent(models.Model):
    """Modèle pour les agents collecteurs"""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='agents/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']


class PointOfSale(models.Model):
    """Modèle principal pour les points de vente enrichi"""
    
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

    POTENTIEL_CHOICES = [
        ('premium', 'Premium stratégique'),
        ('fort', 'Fort potentiel'),
        ('developpement', 'Développement'),
        ('standard', 'Standard'),
    ]

    # Identifiants
    id = models.AutoField(primary_key=True)
    #uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Utilisateur et agent
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='points_of_sale', null=True, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='points_of_sale')
    
    # Informations de base
    name = models.CharField(max_length=200)
    owner = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    
    # Localisation détaillée
    district = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    commune = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100, blank=True, null=True)
    grande_voie = models.BooleanField(default=False, verbose_name="Situé sur une grande voie")
    
    # Typologie et statut
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    potentiel = models.CharField(max_length=20, choices=POTENTIEL_CHOICES, blank=True, null=True)
    
    # Métriques terrain (0-100)
    visibilite = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    accessibilite = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    affluence = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    digitalisation = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Scores d'évaluation (A/D/E)
    score_a = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(25)], verbose_name="Score A - Branding")
    score_d = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(40)], verbose_name="Score D - Commercial")
    score_e = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(35)], verbose_name="Score E - Environnement")
    score_global = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Branding
    brander = models.BooleanField(default=False, verbose_name="Est brandé")
    branding_image = models.ImageField(upload_to='branding/', blank=True, null=True)
    marque_brander = models.CharField(max_length=200, blank=True, null=True, verbose_name="Marque du brander")
    
    # Données commerciales
    monthly_orders = models.PositiveIntegerField(default=0, verbose_name="Commandes mensuelles")
    monthly_turnover = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="CA mensuel (CFA)")
    registration_date = models.DateField()
    date_collecte = models.DateField(auto_now_add=True)
    
    # Qualité des données
    gps_valid = models.BooleanField(default=False, verbose_name="GPS valide")
    fiche_complete = models.BooleanField(default=False, verbose_name="Fiche complète")
    photos_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Point de vente"
        verbose_name_plural = "Points de vente"
        indexes = [
            models.Index(fields=['commune']),
            models.Index(fields=['agent']),
            models.Index(fields=['score_global']),
            models.Index(fields=['brander']),
            models.Index(fields=['potentiel']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"{self.name} - {self.commune}"

    def save(self, *args, **kwargs):
        # Calcul automatique des scores
        self.score_a = self._calculate_score_a()
        self.score_d = self._calculate_score_d()
        self.score_e = self._calculate_score_e()
        self.score_global = self.score_a + self.score_d + self.score_e
        self.potentiel = self._calculate_potentiel()
        self.fiche_complete = self._check_fiche_complete()
        super().save(*args, **kwargs)

    def _calculate_score_a(self):
        """Score A - Branding & disponibilité média (max 25)"""
        base = 10 if self.brander else 14
        visibilite_bonus = int(self.visibilite * 0.09)
        grande_voie_bonus = 3 if self.grande_voie else 0
        return min(25, base + visibilite_bonus + grande_voie_bonus)

    def _calculate_score_d(self):
        """Score D - Potentiel commercial (max 40)"""
        affluence_score = int(self.affluence * 0.25)
        accessibilite_score = int(self.accessibilite * 0.1)
        type_bonus = 6 if self.type in ['demi_grossiste', 'grossiste'] else 0
        return min(40, affluence_score + accessibilite_score + type_bonus)

    def _calculate_score_e(self):
        """Score E - Environnement stratégique (max 35)"""
        visibilite_score = int(self.visibilite * 0.2)
        accessibilite_score = int(self.accessibilite * 0.18)
        grande_voie_bonus = 4 if self.grande_voie else 0
        marche_bonus = 3  # À ajuster selon la proximité d'un marché
        return min(35, visibilite_score + accessibilite_score + grande_voie_bonus + marche_bonus)

    def _calculate_potentiel(self):
        """Calcul du label de potentiel basé sur le score global"""
        if self.score_global >= 85:
            return 'premium'
        elif self.score_global >= 70:
            return 'fort'
        elif self.score_global >= 50:
            return 'developpement'
        return 'standard'

    def _check_fiche_complete(self):
        """Vérifie si la fiche est complète"""
        return all([
            self.name,
            self.address,
            self.latitude is not None,
            self.longitude is not None,
            self.phone,
            self.photos_count >= 4,
        ])

    @property
    def eligibilite_branding(self):
        """Éligibilité pour une offre de branding"""
        return (not self.brander and 
                self.score_global >= 70 and 
                self.visibilite >= 70 and 
                self.accessibilite >= 65)

    @property
    def eligibilite_exclusivite(self):
        """Éligibilité pour une exclusivité"""
        return self.score_global >= 78 and self.affluence >= 72

    @property
    def eligibilite_activation(self):
        """Éligibilité pour une activation promotionnelle"""
        return self.visibilite >= 68 and self.affluence >= 60


class Photo(models.Model):
    """Galerie de photos du point de vente"""
    
    PHOTO_TYPES = [
        ('facade', 'Façade'),
        ('interior', 'Intérieur'),
        ('main_road', 'Axe principal'),
        ('environment', 'Environnement'),
    ]
    
    point_of_sale = models.ForeignKey(PointOfSale, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='pdv_photos/')
    thumbnail = models.ImageField(upload_to='pdv_photos/thumbnails/', blank=True, null=True)
    type = models.CharField(max_length=20, choices=PHOTO_TYPES)
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        unique_together = ['point_of_sale', 'order']

    def __str__(self):
        return f"Photo {self.type} - {self.point_of_sale.name}"


class AgentPerformance(models.Model):
    """Performance des agents collecteurs"""
    
    agent = models.OneToOneField(Agent, on_delete=models.CASCADE, related_name='performance')
    
    total_collecte = models.PositiveIntegerField(default=0)
    gps_valid_count = models.PositiveIntegerField(default=0)
    complete_count = models.PositiveIntegerField(default=0)
    total_photos = models.PositiveIntegerField(default=0)
    
    gps_rate = models.FloatField(default=0.0)
    complete_rate = models.FloatField(default=0.0)
    photo_avg = models.FloatField(default=0.0)
    
    updated_at = models.DateTimeField(auto_now=True)

    def update_performance(self):
        """Met à jour les indicateurs de performance"""
        pdvs = self.agent.points_of_sale.all()
        self.total_collecte = pdvs.count()
        self.gps_valid_count = pdvs.filter(gps_valid=True).count()
        self.complete_count = pdvs.filter(fiche_complete=True).count()
        self.total_photos = sum(p.photos_count for p in pdvs)
        
        self.gps_rate = (self.gps_valid_count / self.total_collecte * 100) if self.total_collecte > 0 else 0
        self.complete_rate = (self.complete_count / self.total_collecte * 100) if self.total_collecte > 0 else 0
        self.photo_avg = (self.total_photos / self.total_collecte) if self.total_collecte > 0 else 0
        
        self.save()


class EvaluationHistory(models.Model):
    """Historique des évaluations pour tracking"""
    
    point_of_sale = models.ForeignKey(PointOfSale, on_delete=models.CASCADE, related_name='evaluations')
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True)
    
    score_a = models.IntegerField()
    score_d = models.IntegerField()
    score_e = models.IntegerField()
    score_global = models.IntegerField()
    
    visibilite = models.IntegerField()
    accessibilite = models.IntegerField()
    affluence = models.IntegerField()
    digitalisation = models.IntegerField()
    
    periode = models.CharField(max_length=7)  # Format: YYYY-MM
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Activation(models.Model):
    """Activations commerciales"""
    
    TYPE_CHOICES = [
        ('branding', 'Branding'),
        ('exclusivite', 'Exclusivité'),
        ('activation_promo', 'Activation promo'),
    ]
    
    STATUS_CHOICES = [
        ('planifie', 'Planifié'),
        ('en_cours', 'En cours'),
        ('realise', 'Réalisé'),
        ('annule', 'Annulé'),
    ]
    
    point_of_sale = models.ForeignKey(PointOfSale, on_delete=models.CASCADE, related_name='activations')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planifie')
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    montant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


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
    tableau = models.BooleanField(default=False, verbose_name="Tableau de bord")
    distributeurs = models.BooleanField(default=False, verbose_name="Distributeurs")
    commerciaux = models.BooleanField(default=False, verbose_name="Commerciaux")
    prospects = models.BooleanField(default=False, verbose_name="Prospects")
    positions = models.BooleanField(default=False, verbose_name="Positions")
    createcommande = models.BooleanField(default=False, verbose_name="Createcommande")
    vuecommande = models.BooleanField(default=False, verbose_name="Vuecommande")
    inventaire = models.BooleanField(default=False, verbose_name="Inventaire")
    commande = models.BooleanField(default=False, verbose_name="Commandes")
    utilisateur = models.BooleanField(default=False, verbose_name="Utilisateurs")
    analytique = models.BooleanField(default=False, verbose_name="Analytiques")
    geolocalisation = models.BooleanField(default=False, verbose_name="Geolocalisations")
    configuration = models.BooleanField(default=False, verbose_name="Configurations")
    dashboard_analytique = models.BooleanField(default=False, verbose_name="Dashboard_analytique")
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
    # date_joined = models.DateField(default=timezone.now)
    date_joined = models.DateTimeField(default=timezone.now)  # Changed from DateField
    last_activity = models.DateTimeField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
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
        
        # CORRECTION : Initialiser quantity_restante SI nécessaire
        if self.quantity_assignes > 0 and self.quantity_restante == 0 and self.quantity_sales == 0:
            self.quantity_restante = self.quantity_assignes
            print(f"🔧 Initialisation dans clean(): {self.quantity_restante}")
        
        # Si c'est un réapprovisionnement, s'assurer que quantity_restante est initialisée
        if (self.activity_type == 'stock_replenishment' and 
            self.quantity_assignes > 0 and 
            self.quantity_restante == 0):
            self.quantity_restante = self.quantity_assignes
        
        # Validation : quantity_restante ne peut pas être > quantity_assignes
        if self.quantity_restante > self.quantity_assignes:
            raise ValidationError("La quantité restante ne peut pas dépasser la quantité assignée")
        
        # CORRECTION : Validation plus intelligente
        total = self.quantity_sales + self.quantity_restante
        
        # Permettre une petite tolérance pour les arrondis/calculs
        if abs(total - self.quantity_assignes) > 1:  # Tolérance de 1 unité
            raise ValidationError(
                f"Incohérence : ventes ({self.quantity_sales}) + "
                f"restantes ({self.quantity_restante}) = {total}, mais "
                f"assignées = {self.quantity_assignes}"
            )
        
        # Validation que les quantités ne sont pas négatives
        if self.quantity_restante < 0:
            raise ValidationError("La quantité restante ne peut pas être négative")
        
        if self.quantity_sales < 0:
            raise ValidationError("La quantité vendue ne peut pas être négative")

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour gérer l'affectation automatique
        """
        # CORRECTION: Initialiser quantity_restante de manière plus robuste
        if self.quantity_assignes > 0:
            if self.quantity_restante == 0 and self.quantity_sales == 0:
                # Cas : nouvelle activité, pas encore de ventes
                self.quantity_restante = self.quantity_assignes
                print(f"🔧 Initialisation quantity_restante: {self.quantity_restante}")
            elif self.quantity_restante > self.quantity_assignes:
                # Cas : incohérence détectée
                self.quantity_restante = max(0, self.quantity_assignes - self.quantity_sales)
                print(f"🔧 Correction quantity_restante: {self.quantity_restante}")
        
        # Validation avant sauvegarde
        try:
            self.clean()
        except ValidationError as e:
            print(f"❌ Validation error in save: {e}")
            # Essayons de corriger automatiquement
            if "Incohérence" in str(e):
                self.quantity_restante = max(0, self.quantity_assignes - self.quantity_sales)
                print(f"🔧 Auto-correction: quantity_restante = {self.quantity_restante}")
            else:
                raise e
        
        # Le reste de votre code save() existant...
        # Si c'est une NOUVELLE activité de réapprovisionnement avec commande
        if (self._state.adding and 
            self.activity_type == 'stock_replenishment' and 
            self.quantity_assignes > 0 and
            self.related_order):
            
            print(f"🔧 Création activité réapprovisionnement - Quantité: {self.quantity_assignes}")
            
            # VÉRIFICATION PRÉALABLE : Est-ce qu'il y a au moins un article qui peut être affecté ?
            peut_etre_affecte = any(item.quantite_restante() > 0 for item in self.related_order.items.all())
            if not peut_etre_affecte:
                error_msg = "ABANDON : Aucun article dans la commande ne nécessite une affectation (tous sont déjà complètement affectés)"
                print(f"❌ {error_msg}")
                raise ValidationError(error_msg)
            
            # Sauvegarder d'abord pour avoir un ID
            super().save(*args, **kwargs)
            
            # Ensuite affecter la quantité aux articles
            try:
                self.affecter_quantite_commande()
                print(f"✅ Activité créée avec SUCCÈS")
                
            except ValidationError as e:
                print(f"❌ ERREUR CRITIQUE lors de l'affectation: {e}")
                # En cas d'erreur, supprimer l'instance créée
                print("🗑️ Suppression de l'activité créée à cause de l'échec de l'affectation")
                self.delete()
                raise ValidationError(f"Échec de la création de l'activité : {e}")
                
        else:
            # Pour les autres cas (mise à jour ou autres types)
            super().save(*args, **kwargs)

    def affecter_quantite_commande(self):
        """
        Affecte la quantité assignée aux articles de la commande
        """
        if not self.related_order:
            print("❌ Aucune commande liée")
            raise ValidationError("Aucune commande liée pour l'affectation")
            
        print(f"🔧 Début affectation - Quantité à affecter: {self.quantity_assignes}")
        
        order_items = self.related_order.items.all()
        if not order_items.exists():
            print("❌ Aucun article dans la commande")
            raise ValidationError("La commande liée ne contient aucun article")
            
        quantite_restante_apres_affectation = self.quantity_assignes
        total_affecte = 0
        
        print(f"📦 Nombre d'articles dans la commande: {order_items.count()}")
        
        for item in order_items:
            if quantite_restante_apres_affectation <= 0:
                break
                
            # Vérifier si l'article a besoin d'être affecté
            quantite_restante_item = item.quantite_restante()
            print(f"   📋 Article {item.id}: {quantite_restante_item} unités restantes à affecter")
            
            if quantite_restante_item > 0:
                quantite_a_affecter = min(quantite_restante_apres_affectation, quantite_restante_item)
                
                print(f"   ➕ Article {item.id}: affectation de {quantite_a_affecter} unités")
                
                try:
                    # Affecter la quantité à l'article
                    item.affecter_quantite(quantite_a_affecter)
                    quantite_restante_apres_affectation -= quantite_a_affecter
                    total_affecte += quantite_a_affecter
                    print(f"   ✅ Affecté: {quantite_a_affecter}, Reste à affecter: {quantite_restante_apres_affectation}")
                except ValidationError as e:
                    print(f"   ❌ Erreur d'affectation pour l'article {item.id}: {e}")
                    continue
            else:
                print(f"   ⏭️ Article {item.id}: déjà complètement affecté, passage au suivant")
        
        # CORRECTION CRITIQUE : Si AUCUNE unité n'a pu être affectée, on lève une exception
        if total_affecte == 0:
            error_msg = (
                f"IMPOSSIBLE de créer l'activité : Aucune unité n'a pu être affectée sur {self.quantity_assignes} demandées. "
                f"Raisons possibles : "
                f"- Tous les articles de la commande sont déjà complètement affectés "
                f"- La commande ne contient pas d'articles nécessitant une affectation "
                f"- Les quantités restantes des articles sont nulles"
            )
            print(f"❌ {error_msg}")
            raise ValidationError(error_msg)
        
        # Mettre à jour la quantité restante
        self.quantity_restante = quantite_restante_apres_affectation
        print(f"🔧 Affectation terminée avec SUCCÈS:")
        print(f"   ✅ Total affecté: {total_affecte} unités sur {self.quantity_assignes}")
        print(f"   📊 Quantité restante après affectation: {self.quantity_restante}")
        
        # Sauvegarder la quantité restante mise à jour
        super().save(update_fields=['quantity_restante'])
        
        if quantite_restante_apres_affectation > 0:
            warning_msg = f"{quantite_restante_apres_affectation} unités n'ont pas pu être affectées (stock insuffisant dans les articles)"
            print(f"   ⚠️ {warning_msg}")
            # Dans ce cas, on ne lève pas d'exception car au moins une partie a été affectée

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
        locked_activity = VendorActivity.objects.select_for_update().get(id=self.id)
        
        print(f"🔒 Verrouillage activité {locked_activity.id}")
        print(f"   Quantité demandée: {quantite}")
        print(f"   Quantité restante actuelle: {locked_activity.quantity_restante}")
        print(f"   Quantité assignée: {locked_activity.quantity_assignes}")
        print(f"   Quantité déjà vendue: {locked_activity.quantity_sales}")
        
        # CORRECTION CRITIQUE : Vérification et correction systématique
        quantite_calculee_restante = locked_activity.quantity_assignes - locked_activity.quantity_sales
        
        # Si incohérence détectée, corriger IMMÉDIATEMENT et SAUVEGARDER
        if quantite_calculee_restante != locked_activity.quantity_restante:
            print(f"⚠️ Incohérence détectée: restante={locked_activity.quantity_restante}, calculée={quantite_calculee_restante}")
            
            # Appliquer la correction
            ancienne_valeur = locked_activity.quantity_restante
            locked_activity.quantity_restante = max(0, quantite_calculee_restante)
            
            print(f"🔧 Correction appliquée: {ancienne_valeur} → {locked_activity.quantity_restante}")
            
            # CORRECTION : SAUVEGARDER LA CORRECTION avant de continuer
            locked_activity.save(update_fields=['quantity_restante'])
            print(f"💾 Correction sauvegardée en base")
            
            # Vérification de sécurité après correction
            if locked_activity.quantity_restante < 0:
                raise ValidationError(f"Quantité restante devenue négative après correction: {locked_activity.quantity_restante}")
        
        # VÉRIFICATION FINALE AVANT VENTE
        if quantite > locked_activity.quantity_restante:
            raise ValidationError(
                f"Stock insuffisant. Demande: {quantite}, Disponible: {locked_activity.quantity_restante}"
            )
        
        if locked_activity.quantity_restante == 0:
            raise ValidationError("Stock épuisé, impossible de vendre")
        
        # Mise à jour atomique
        locked_activity.quantity_sales += quantite
        locked_activity.quantity_restante -= quantite
        
        # Validation rigoureuse des nouvelles valeurs
        if locked_activity.quantity_restante < 0:
            raise ValidationError(f"Quantité restante négative après vente: {locked_activity.quantity_restante}")
        
        if locked_activity.quantity_sales > locked_activity.quantity_assignes:
            raise ValidationError(
                f"Ventes ({locked_activity.quantity_sales}) > assignées ({locked_activity.quantity_assignes})"
            )
        
        # Vérification de cohérence finale
        if locked_activity.quantity_sales + locked_activity.quantity_restante != locked_activity.quantity_assignes:
            raise ValidationError(
                f"Incohérence après vente: {locked_activity.quantity_sales} + {locked_activity.quantity_restante} != {locked_activity.quantity_assignes}"
            )
        
        # CORRECTION: Sauvegarde avec validation complète
        locked_activity.save()
        
        print(f"✅ Vente effectuée avec succès:")
        print(f"   Quantité vendue: {quantite}")
        print(f"   Nouvelles ventes totales: {locked_activity.quantity_sales}")
        print(f"   Nouvelle quantité restante: {locked_activity.quantity_restante}")
        print(f"   Vérification: {locked_activity.quantity_sales} + {locked_activity.quantity_restante} = {locked_activity.quantity_assignes}")
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


# class Sale(models.Model):
#     """
#     Modèle pour enregistrer les ventes
#     """
#     vendor_activity = models.ForeignKey(
#         'VendorActivity', 
#         on_delete=models.CASCADE,
#         related_name='sales'
#     )
#     quantity = models.PositiveIntegerField()
#     price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     customer_name = models.CharField(max_length=100, blank=True, null=True)
#     timestamp = models.DateTimeField(auto_now_add=True)
#     notes = models.TextField(blank=True, null=True)
#     latitude = models.FloatField(blank=True, null=True, verbose_name="Latitude")
#     longitude = models.FloatField(blank=True, null=True, verbose_name="Longitude")
    
#     class Meta:
#         verbose_name = "Vente"
#         verbose_name_plural = "Ventes"
#         ordering = ['-timestamp']
    
#     def clean(self):
#         """Validation avant sauvegarde"""
#         super().clean()
        
#         if self.quantity <= 0:
#             raise ValidationError("La quantité doit être positive")
        
#         if not self.vendor_activity:
#             raise ValidationError("Une activité de vendeur est requise")
    
#     def save(self, *args, **kwargs):
#         """
#         Surcharge de save() pour gérer automatiquement les ventes
#         """
#         # Validation
#         self.clean()
        
#         # Si c'est une nouvelle vente
#         if self._state.adding:
#             print(f"💰 Création nouvelle vente: {self.quantity} unités")
            
#             # Utiliser la méthode atomique pour effectuer la vente
#             try:
#                 self.vendor_activity.vendre_avec_verrouillage(self.quantity)
#                 print(f"✅ Stock mis à jour avec succès")
#             except ValidationError as e:
#                 print(f"❌ Erreur lors de la vente: {e}")
#                 raise e
        
#         # Sauvegarder la vente
#         super().save(*args, **kwargs)
#         print(f"💾 Vente sauvegardée: ID={self.id}")
    
#     def __str__(self):
#         return f"Vente {self.quantity} unités - {self.vendor_activity.vendor.full_name} - {self.created_at.date()}"
    
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
    phone = models.CharField(max_length=100, blank=True, verbose_name="Type de pushcard",unique=True)

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
    latitude = models.FloatField(blank=True, null=True, verbose_name="Latitude")
    longitude = models.FloatField(blank=True, null=True, verbose_name="Longitude")
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
        return f"Vente {self.quantity} unités - {self.vendor_activity.vendor.full_name}"
    
class SalePOS(models.Model):
    """
    Modèle pour enregistrer les ventes
    """
    product_variant = models.ForeignKey(
        'ProductVariant',
        on_delete=models.CASCADE,
        related_name='salespos'
    )
    customer = models.ForeignKey(
        'PointOfSale',
        on_delete=models.CASCADE,
        related_name='purchasespos'
    )
    quantity = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    latitude = models.FloatField(blank=True, null=True, verbose_name="Latitude")
    longitude = models.FloatField(blank=True, null=True, verbose_name="Longitude")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    vendor = models.ForeignKey(
        'MobileVendor',
        on_delete=models.CASCADE,
        related_name='sales_vendorspos'
    )
    vendor_activity = models.ForeignKey(
        'VendorActivity', 
        on_delete=models.CASCADE,
        related_name='salespos'
    )
    
    class Meta:
        db_table = 'salespos'
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
        return f"Vente {self.quantity} unités - {self.vendor_activity.vendor.full_name}"
    

# models.py - Ajoutez cette classe
class Report(models.Model):
    """
    Modèle pour stocker les rapports générés
    """
    REPORT_TYPES = [
        ('ventes', 'Rapport des Ventes'),
        ('stocks', 'Rapport des Stocks'),
        ('commandes', 'Rapport des Commandes'),
        ('clients', 'Rapport des Clients'),
        ('fournisseurs', 'Rapport des Fournisseurs'),
        ('vendeurs', 'Rapport des Vendeurs Ambulants'),
        ('points_vente', 'Rapport des Points de Vente'),
        ('performance', 'Rapport de Performance'),
    ]

    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
    ]

    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    point_of_sale = models.ForeignKey(PointOfSale, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    filters = models.JSONField(default=dict)  # Pour stocker les filtres appliqués
    data = models.JSONField()  # Données du rapport
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    size = models.CharField(max_length=50, default='0 KB')
    is_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rapport"
        verbose_name_plural = "Rapports"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_report_type_display()}"

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = f"Rapport {self.get_report_type_display()} {self.start_date} - {self.end_date}"
        super().save(*args, **kwargs)

    def get_file_size(self):
        if self.file and hasattr(self.file, 'size'):
            size = self.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "0 KB"
    

class District(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['nom']
    
    def __str__(self):
        return self.nom

class Ville(models.Model):
    nom = models.CharField(max_length=100)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='villes')
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['nom']
        unique_together = ['nom', 'district']
    
    def __str__(self):
        return f"{self.nom} - {self.district.nom}"

class Quartier(models.Model):
    nom = models.CharField(max_length=100)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, related_name='quartiers')
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['nom']
        unique_together = ['nom', 'ville']
    
    def __str__(self):
        return f"{self.nom} - {self.ville.nom}"