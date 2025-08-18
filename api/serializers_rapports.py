from rest_framework import serializers
from django.db.models import Sum, Count, F, ExpressionWrapper, FloatField
from django.db.models.functions import TruncMonth, TruncDay
from .models import (
    Product, ProductVariant, Order, OrderItem, 
    StockMovement, PointOfSale, Category
)
from datetime import datetime, timedelta

class SalesReportSerializer(serializers.Serializer):
    period = serializers.CharField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    best_selling_products = serializers.ListField()
    
class InventoryReportSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    low_stock_items = serializers.IntegerField()
    out_of_stock_items = serializers.IntegerField()
    overstocked_items = serializers.IntegerField()
    stock_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    
class POSPerformanceSerializer(serializers.ModelSerializer):
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_orders = serializers.IntegerField()
    
    class Meta:
        model = PointOfSale
        fields = ['id', 'name', 'type', 'region', 'total_sales', 'total_orders']
        
class CategorySalesSerializer(serializers.ModelSerializer):
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    percentage = serializers.FloatField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'total_sales', 'percentage']