# serializers.py
from rest_framework import serializers
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import *

class ReportSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé général"""
    total_points_of_sale = serializers.IntegerField()
    active_points_of_sale = serializers.IntegerField()
    total_products = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()
    out_of_stock_products = serializers.IntegerField()
    total_mobile_vendors = serializers.IntegerField()
    active_mobile_vendors = serializers.IntegerField()
    total_sales_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()

class SalesReportSerializer(serializers.Serializer):
    """Serializer pour les rapports de vente"""
    period = serializers.CharField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_quantity_sold = serializers.IntegerField()
    average_sale_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    sales_growth = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)

class TopProductSerializer(serializers.Serializer):
    """Serializer pour les produits les plus vendus"""
    product_name = serializers.CharField()
    category_name = serializers.CharField()
    total_quantity_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    point_of_sale_name = serializers.CharField()

class VendorPerformanceSerializer(serializers.Serializer):
    """Serializer pour la performance des vendeurs"""
    vendor_name = serializers.CharField()
    point_of_sale_name = serializers.CharField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_quantity_sold = serializers.IntegerField()
    performance_score = serializers.FloatField()
    average_daily_sales = serializers.DecimalField(max_digits=10, decimal_places=2)
    zone = serializers.CharField()

class StockAlertSerializer(serializers.Serializer):
    """Serializer pour les alertes de stock"""
    id = serializers.IntegerField()
    product_name = serializers.CharField()
    point_of_sale_name = serializers.CharField()
    format_name = serializers.CharField(allow_null=True)
    current_stock = serializers.IntegerField()
    min_stock = serializers.IntegerField()
    max_stock = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)

class OrderReportSerializer(serializers.Serializer):
    """Serializer pour les rapports de commande"""
    id = serializers.IntegerField()
    customer_name = serializers.CharField()
    point_of_sale_name = serializers.CharField()
    status = serializers.CharField()
    total = serializers.DecimalField(max_digits=15, decimal_places=2)
    date = serializers.DateField()
    delivery_date = serializers.DateField(allow_null=True)
    priority = serializers.CharField()
    items_count = serializers.IntegerField()

class FinancialReportSerializer(serializers.Serializer):
    """Serializer pour les rapports financiers"""
    period = serializers.CharField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    revenue_growth = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)

# Serializers pour Graphiques
class SalesTrendSerializer(serializers.Serializer):
    """Serializer pour les tendances de vente"""
    date = serializers.DateField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_quantity = serializers.IntegerField()

class CategorySalesSerializer(serializers.Serializer):
    """Serializer pour les ventes par catégorie"""
    category_name = serializers.CharField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    percentage = serializers.FloatField()

class VendorComparisonSerializer(serializers.Serializer):
    """Serializer pour comparer les vendeurs"""
    vendor_name = serializers.CharField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_quantity = serializers.IntegerField()
    performance = serializers.FloatField()

class StockDistributionSerializer(serializers.Serializer):
    """Serializer pour la distribution des stocks"""
    status = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()

class RevenueTrendSerializer(serializers.Serializer):
    """Serializer pour les tendances de revenus"""
    period = serializers.CharField()
    revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    orders = serializers.IntegerField()

class RealTimeMetricsSerializer(serializers.Serializer):
    """Serializer pour les métriques temps réel"""
    today_sales_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    today_sales_quantity = serializers.IntegerField()
    today_orders = serializers.IntegerField()
    active_vendors_today = serializers.IntegerField()
    urgent_stock_alerts = serializers.IntegerField()
    last_updated = serializers.DateTimeField()