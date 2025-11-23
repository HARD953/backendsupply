from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryListCreateView, CategoryDetailView,
    SupplierListCreateView, SupplierDetailView,
    PointOfSaleListCreateView, PointOfSaleDetailView,
    PermissionListView, PermissionDetailView,
    RoleListCreateView, RoleDetailView,
    ProductListCreateView, ProductDetailView,
    StockMovementListCreateView, StockMovementDetailView,
    OrderListCreateView, OrderDetailView,
    DisputeListCreateView, DisputeDetailView,
    TokenListCreateView, TokenDetailView,
    TokenTransactionListCreateView, TokenTransactionDetailView,
    NotificationListCreateView, NotificationDetailView,
    DashboardView, StockOverviewView,PurchaseViewSetDataPOS,
    ProductFormatListCreateView,ProductFormatDetailView, SaleViewSet,SaleViewSetPOS,
    ProductVariantListCreateView, ProductVariantDetailView  # Nouveaux endpoints ajoutés
)
from .views import MobileVendorViewSet, VendorActivityViewSet, VendorPerformanceViewSet, PurchaseViewSet,VendorActivitySummaryViewSet,PurchaseViewSetData

from .views_rapports import (
    SalesAnalyticsView, InventoryStatusView,
    POSPerformanceView, CategorySalesView,
    SalesTrendView
)
#from .viewser import ReportViewSet, DashboardViewSet
from .views import UserProfileViewSet
from .views_per import VendorViewSet
from .views1 import StatisticsViewSet

from . import views
from . import views4

# Création du routeur
router = DefaultRouter()
router.register(r'mobile-vendors', MobileVendorViewSet, basename='mobile-vendor')
router.register(r'vendors', VendorViewSet, basename='vendor')
router.register(r'vendor-activities', VendorActivityViewSet, basename='vendor-activity')
router.register(r'vendor-performances', VendorPerformanceViewSet, basename='vendor-performance')
router.register(r'purchases', PurchaseViewSet, basename='purchase')
router.register(r'vendor-activities-summary', VendorActivitySummaryViewSet, basename='vendor-activity-summary')
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'salespos', SaleViewSetPOS, basename='salepos')
router.register(r'users', UserProfileViewSet)
router.register(r'purchasedata', PurchaseViewSetData, basename='purchases')
router.register(r'purchasedatapos', PurchaseViewSetDataPOS, basename='purchasespos')
router.register(r'statistics', StatisticsViewSet, basename='statistics')

router.register(r'districts', views.DistrictViewSet)
router.register(r'villes', views.VilleViewSet)
router.register(r'quartiers', views.QuartierViewSet)


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
    path('points-vente/<int:pk>/', PointOfSaleDetailView.as_view(), name='point-of-sale-detail'),
    
    # Permissions
    path('permissions/', PermissionListView.as_view(), name='permission-list'),
    path('permissions/<int:pk>/', PermissionDetailView.as_view(), name='permission-detail'),
    
    # Rôles
    path('roles/', RoleListCreateView.as_view(), name='role-list-create'),
    path('roles/<int:pk>/', RoleDetailView.as_view(), name='role-detail'),
    
    # # Utilisateurs
    # path('users/', UserProfileListCreateView.as_view(), name='user-list-create'),
    # path('users/<int:pk>/', UserProfileDetailView.as_view(), name='user-detail'),
    
    # Produits
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:id>/', ProductDetailView.as_view(), name='product-detail'),
    
    # Produits-formats
    path('products-formats/', ProductFormatListCreateView.as_view(), name='product-list-create'),
    path('products-formats/<int:pk>/', ProductFormatDetailView.as_view(), name='product-detail'),

    # Variantes de produits (nouveaux endpoints)
    path('product-variants/', ProductVariantListCreateView.as_view(), name='product-variant-list-create'),
    path('product-variants/<int:id>/', ProductVariantDetailView.as_view(), name='product-variant-detail'),
    
    # Mouvements de stock
    path('stock-movements/', StockMovementListCreateView.as_view(), name='stock-movement-list-create'),
    path('stock-movements/<int:id>/', StockMovementDetailView.as_view(), name='stock-movement-detail'),
    
    # Commandes
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<int:id>/', OrderDetailView.as_view(), name='order-detail'),
    
    # Commandes
    path('ordersitems/', OrderListCreateView.as_view(), name='orderitems-list-create'),
    path('ordersitems/<int:id>/', OrderDetailView.as_view(), name='orderitems-detail'),

    # Litiges
    path('disputes/', DisputeListCreateView.as_view(), name='dispute-list-create'),
    path('disputes/<int:id>/', DisputeDetailView.as_view(), name='dispute-detail'),
    
    # Tokens
    path('tokens/', TokenListCreateView.as_view(), name='token-list-create'),
    path('tokens/<int:id>/', TokenDetailView.as_view(), name='token-detail'),
    
    # Transactions de tokens
    path('token-transactions/', TokenTransactionListCreateView.as_view(), name='token-transaction-list-create'),
    path('token-transactions/<int:id>/', TokenTransactionDetailView.as_view(), name='token-transaction-detail'),
    
    # Notifications
    path('notifications/', NotificationListCreateView.as_view(), name='notification-list-create'),
    path('notifications/<int:id>/', NotificationDetailView.as_view(), name='notification-detail'),

    # Endpoint supplémentaire pour le 
    path('mobile-vendors/dashboard/stats/', MobileVendorViewSet.as_view({'get': 'stats'}), name='mobile-vendors-dashboard-stats'),

    # Endpoint supplémentaire pour le rapports
    path('sales-analytics/', SalesAnalyticsView.as_view(), name='sales-analytics'),
    path('inventory-status/', InventoryStatusView.as_view(), name='inventory-status'),
    path('pos-performance/', POSPerformanceView.as_view(), name='pos-performance'),
    path('category-sales/', CategorySalesView.as_view(), name='category-sales'),
    path('sales-trend/', SalesTrendView.as_view(), name='sales-trend'),
    path('carte/', views.get_customer_sales, name='customer-sales-sales'),
    path('pointsaleorders/', views.get_point_of_sale_orders_simple, name='pos-orders-simple'),

    # Routes spécifiques pour un accès rapide
    path('statistics/dashboard_summary/', StatisticsViewSet.as_view({'get': 'dashboard_summary'})),
    path('statistics/points_of_sale_stats/', StatisticsViewSet.as_view({'get': 'points_of_sale_stats'})),
    path('statistics/mobile_vendors_stats/', StatisticsViewSet.as_view({'get': 'mobile_vendors_stats'})),
    path('statistics/products_stats/', StatisticsViewSet.as_view({'get': 'products_stats'})),
    path('statistics/sales_timeseries/', StatisticsViewSet.as_view({'get': 'sales_timeseries'})),
    path('statistics/performance_metrics/', StatisticsViewSet.as_view({'get': 'performance_metrics'})),

    path('statistics/purchase_stat/', StatisticsViewSet.as_view({'get': 'top_purchases_stats'})),
    path('statistics/top_purchase/', StatisticsViewSet.as_view({'get': 'top_purchases_by_vendor'})),

        # Nouvelles URLs pour graphiques et exports
    path('statistics/sales_chart/', StatisticsViewSet.as_view({'get': 'sales_chart'})),
    path('statistics/performance_chart/', StatisticsViewSet.as_view({'get': 'performance_chart'})),
    path('statistics/export_data/', StatisticsViewSet.as_view({'post': 'export_data'})),

    path('me/', views4.get_current_user_profile, name='user-profile'),

    path('', include(router.urls)),
]
