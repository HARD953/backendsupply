from rest_framework import serializers
from django.db.models import Sum, Count, Avg, F, Q, When, Case, Value, IntegerField
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, ExtractWeek, ExtractMonth
from django.utils import timezone
from datetime import timedelta
from .models import (
    Product, ProductVariant, Order, OrderItem, PointOfSale, 
    Category, Supplier, UserProfile, MobileVendor, VendorActivity, Purchase, Sale
)

class ReportFilterSerializer(serializers.Serializer):
    """Serializer pour les filtres de rapport"""
    report_type = serializers.ChoiceField(choices=[
        ('ventes', 'Ventes'),
        ('stocks', 'Stocks'),
        ('clients', 'Clients'),
        ('performance', 'Performance'),
        ('commandes', 'Commandes'),
        ('fournisseurs', 'Fournisseurs')
    ], required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    point_of_sale = serializers.PrimaryKeyRelatedField(
        queryset=PointOfSale.objects.all(), required=False
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), required=False
    )
    vendor = serializers.PrimaryKeyRelatedField(
        queryset=MobileVendor.objects.all(), required=False
    )

class SalesReportSerializer(serializers.Serializer):
    """Serializer pour le rapport des ventes"""
    total = serializers.DecimalField(max_digits=15, decimal_places=2)
    evolution = serializers.CharField()
    point_of_sale = serializers.CharField()
    chart_data = serializers.ListField()
    by_product = serializers.ListField()
    by_category = serializers.ListField()
    table_data = serializers.ListField()

class StockReportSerializer(serializers.Serializer):
    """Serializer pour le rapport des stocks"""
    total_products = serializers.IntegerField()
    low_stock = serializers.IntegerField()
    point_of_sale = serializers.CharField()
    chart_data = serializers.ListField()
    by_category = serializers.ListField()
    status_distribution = serializers.ListField()

class ClientReportSerializer(serializers.Serializer):
    """Serializer pour le rapport clients"""
    new_clients = serializers.IntegerField()
    returning_clients = serializers.IntegerField()
    point_of_sale = serializers.CharField()
    chart_data = serializers.ListField()
    by_region = serializers.ListField()
    by_commune = serializers.ListField()

class OrderReportSerializer(serializers.Serializer):
    """Serializer pour le rapport des commandes"""
    total_orders = serializers.IntegerField()
    completed = serializers.IntegerField()
    pending = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    point_of_sale = serializers.CharField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    chart_data = serializers.ListField()
    by_status = serializers.ListField()
    by_category = serializers.ListField()

class SupplierReportSerializer(serializers.Serializer):
    """Serializer pour le rapport fournisseurs"""
    total_suppliers = serializers.IntegerField()
    active_suppliers = serializers.IntegerField()
    total_products = serializers.IntegerField()
    point_of_sale = serializers.CharField()
    chart_data = serializers.ListField()
    by_supplier = serializers.ListField()
    by_category = serializers.ListField()

class GeneratedReportSerializer(serializers.Serializer):
    """Serializer pour les rapports générés"""
    id = serializers.IntegerField()
    title = serializers.CharField()
    type = serializers.CharField()
    period = serializers.CharField()
    generated_at = serializers.DateTimeField()
    download_url = serializers.CharField()
    size = serializers.CharField()
    data = serializers.DictField()