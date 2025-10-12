# serializers.py
from rest_framework import serializers
from django.db.models import Sum, Count, Avg, F, Window
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from .models import *

class StatisticSerializer(serializers.Serializer):
    """Serializer de base pour les statistiques"""
    period = serializers.CharField()
    value = serializers.DecimalField(max_digits=15, decimal_places=2)
    growth = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    previous_value = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)

class POSStatisticSerializer(serializers.ModelSerializer):
    """Serializer pour les stats des points de vente"""
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    mobile_vendors_count = serializers.IntegerField()
    performance_score = serializers.FloatField()
    
    class Meta:
        model = PointOfSale
        fields = [
            'id', 'name', 'type', 'region', 'commune', 
            'total_sales', 'total_orders', 'average_order_value',
            'mobile_vendors_count', 'performance_score', 'turnover'
        ]

class MobileVendorStatisticSerializer(serializers.ModelSerializer):
    """Serializer pour les stats des vendeurs ambulants"""
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_purchases = serializers.IntegerField()
    average_purchase_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    active_days = serializers.IntegerField()
    efficiency_rate = serializers.FloatField()
    
    class Meta:
        model = MobileVendor
        fields = [
            'id', 'full_name', 'phone', 'status', 'vehicle_type',
            'total_sales', 'total_purchases', 'average_purchase_value',
            'active_days', 'efficiency_rate', 'performance'
        ]

class ProductStatisticSerializer(serializers.ModelSerializer):
    """Serializer pour les stats des produits"""
    total_quantity_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock_rotation = serializers.FloatField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'status',
            'total_quantity_sold', 'total_revenue', 'average_price',
            'stock_rotation'
        ]

class PurchaseStatisticSerializer(serializers.ModelSerializer):
    """Serializer pour les stats des achats"""
    vendor_name = serializers.CharField(source='vendor.full_name')
    zone = serializers.CharField()
    purchase_count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    class Meta:
        model = Purchase
        fields = [
            'id', 'vendor_name', 'first_name', 'last_name', 'zone',
            'purchase_count', 'total_amount', 'purchase_date', 'base'
        ]

class TimeSeriesSerializer(serializers.Serializer):
    """Serializer pour les séries temporelles"""
    date = serializers.DateField()
    value = serializers.DecimalField(max_digits=15, decimal_places=2)
    label = serializers.CharField(required=False)

class DashboardSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé du dashboard"""
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_orders = serializers.IntegerField()
    total_mobile_vendors = serializers.IntegerField()
    total_points_of_sale = serializers.IntegerField()
    active_purchases = serializers.IntegerField()
    sales_growth = serializers.DecimalField(max_digits=5, decimal_places=2)
    revenue_growth = serializers.DecimalField(max_digits=5, decimal_places=2)