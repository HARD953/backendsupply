from django.urls import path, include
from .views import (
    CategoryListCreateView, CategoryDetailView,
    SupplierListCreateView, SupplierDetailView,
    PointOfSaleListCreateView, PointOfSaleDetailView,
    PermissionListView, PermissionDetailView,
    RoleListCreateView, RoleDetailView,
    UserProfileListCreateView, UserProfileDetailView,
    ProductListCreateView, ProductDetailView,
    StockMovementListCreateView, StockMovementDetailView,
    OrderListCreateView, OrderDetailView,
    DisputeListCreateView, DisputeDetailView,
    TokenListCreateView, TokenDetailView,
    TokenTransactionListCreateView, TokenTransactionDetailView,
    NotificationListCreateView, NotificationDetailView,
    DashboardView, StockOverviewView,
    ProductFormatListCreateView,ProductFormatDetailView,
    ProductVariantListCreateView, ProductVariantDetailView  # Nouveaux endpoints ajoutés

)
from .views import MobileVendorViewSet, VendorActivityViewSet, VendorPerformanceViewSet

from rest_framework.routers import DefaultRouter
# Création du routeur
router = DefaultRouter()

router.register(r'mobile-vendors', MobileVendorViewSet, basename='mobile-vendor')
router.register(r'vendor-activities', VendorActivityViewSet, basename='vendor-activity')
router.register(r'vendor-performances', VendorPerformanceViewSet, basename='vendor-performance')

urlpatterns = [
    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # Stock Overview
    path('stock-overview/', StockOverviewView.as_view(), name='stock-overview'),
    
    # Categories
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    
    # Suppliers
    path('suppliers/', SupplierListCreateView.as_view(), name='supplier-list-create'),
    path('suppliers/<int:pk>/', SupplierDetailView.as_view(), name='supplier-detail'),
    
    # Points de vente
    path('points-vente/', PointOfSaleListCreateView.as_view(), name='point-of-sale-list-create'),
    path('points-vente/<uuid:pk>/', PointOfSaleDetailView.as_view(), name='point-of-sale-detail'),
    
    # Permissions
    path('permissions/', PermissionListView.as_view(), name='permission-list'),
    path('permissions/<str:pk>/', PermissionDetailView.as_view(), name='permission-detail'),
    
    # Rôles
    path('roles/', RoleListCreateView.as_view(), name='role-list-create'),
    path('roles/<str:pk>/', RoleDetailView.as_view(), name='role-detail'),
    
    # Utilisateurs
    path('users/', UserProfileListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserProfileDetailView.as_view(), name='user-detail'),
    
    # Produits
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<uuid:pk>/', ProductDetailView.as_view(), name='product-detail'),
    
    # Produits-formats
    path('products-formats/', ProductFormatListCreateView.as_view(), name='product-list-create'),
    path('products-formats/<str:pk>/', ProductFormatDetailView.as_view(), name='product-detail'),

    # Variantes de produits (nouveaux endpoints)
    path('product-variants/', ProductVariantListCreateView.as_view(), name='product-variant-list-create'),
    path('product-variants/<uuid:pk>/', ProductVariantDetailView.as_view(), name='product-variant-detail'),
    
    # Mouvements de stock
    path('stock-movements/', StockMovementListCreateView.as_view(), name='stock-movement-list-create'),
    path('stock-movements/<uuid:pk>/', StockMovementDetailView.as_view(), name='stock-movement-detail'),
    
    # Commandes
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<str:pk>/', OrderDetailView.as_view(), name='order-detail'),
    
    # Litiges
    path('disputes/', DisputeListCreateView.as_view(), name='dispute-list-create'),
    path('disputes/<uuid:pk>/', DisputeDetailView.as_view(), name='dispute-detail'),
    
    # Tokens
    path('tokens/', TokenListCreateView.as_view(), name='token-list-create'),
    path('tokens/<uuid:pk>/', TokenDetailView.as_view(), name='token-detail'),
    
    # Transactions de tokens
    path('token-transactions/', TokenTransactionListCreateView.as_view(), name='token-transaction-list-create'),
    path('token-transactions/<uuid:pk>/', TokenTransactionDetailView.as_view(), name='token-transaction-detail'),
    
    # Notifications
    path('notifications/', NotificationListCreateView.as_view(), name='notification-list-create'),
    path('notifications/<uuid:pk>/', NotificationDetailView.as_view(), name='notification-detail'),

    path('', include(router.urls)),

    # Endpoint supplémentaire pour le dashboard
    path('mobile-vendors/dashboard/stats/', MobileVendorViewSet.as_view({'get': 'stats'}), name='mobile-vendors-dashboard-stats'),
]

# # Créer répertoire et environnement virtuel
# mkdir lanfiatech-backend
# cd lanfiatech-backend
# python -m venv venv
# source venv/bin/activate  # ou venv\Scripts\activate sur Windows

# # Installer les packages
# pip install django djangorestframework django-filter pillow
# pip freeze > requirements.txt

# # Créer projet et application
# django-admin startproject lanfiatech .
# python manage.py startapp api

# # Ajouter 'rest_framework' et 'api' à INSTALLED_APPS dans settings.py

# # Appliquer migrations
# python manage.py makemigrations
# python manage.py migrate

# # Créer superutilisateur
# python manage.py createsuperuser

# # Lancer le serveur
# python manage.py runserver