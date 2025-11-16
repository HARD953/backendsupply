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


# serializers.py
from rest_framework import serializers
from .models import Purchase, Sale, ProductVariant, Product, ProductFormat

class ProductFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductFormat
        fields = ['id', 'name', 'description']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'category', 'status']

class ProductVariantDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    format = ProductFormatSerializer(read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product', 'format', 'current_stock', 
            'price', 'barcode'
        ]

class SaleDetailSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantDetailSerializer(read_only=True)
    vendor = serializers.StringRelatedField()
    unit_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Sale
        fields = [
            'id', 'product_variant', 'quantity', 'total_amount',
            'unit_price', 'created_at', 'vendor','latitude','longitude'
        ]
    
    def get_unit_price(self, obj):
        if obj.quantity > 0:
            return obj.total_amount / obj.quantity
        return 0

class PurchaseSummarySerializer(serializers.ModelSerializer):
    total_sales_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_sales_quantity = serializers.IntegerField(read_only=True)
    sales_count = serializers.IntegerField(read_only=True)
    total_products = serializers.IntegerField(read_only=True)
    total_variants = serializers.IntegerField(read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    average_sale_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Purchase
        fields = [
            'id', 'full_name', 'first_name', 'last_name', 'zone',
            'vendor', 'vendor_name', 'purchase_date', 'base',
            'pushcard_type', 'phone', 'latitude', 'longitude',
            'total_sales_amount', 'total_sales_quantity', 'sales_count',
            'total_products', 'total_variants', 'average_sale_amount',
            'created_at'
        ]
    
    def get_average_sale_amount(self, obj):
        if obj.sales_count > 0:
            return obj.total_sales_amount / obj.sales_count
        return 0
    
class PurchaseSummarySerializerPOS(serializers.ModelSerializer):
    total_sales_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_sales_quantity = serializers.IntegerField(read_only=True)
    sales_count = serializers.IntegerField(read_only=True)
    total_products = serializers.IntegerField(read_only=True)
    total_variants = serializers.IntegerField(read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    average_sale_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = PointOfSale
        # fields = [
        #     'id', 'full_name', 'first_name', 'last_name', 'zone',
        #     'vendor', 'vendor_name', 'purchase_date', 'base',
        #     'pushcard_type', 'phone', 'latitude', 'longitude',
        #     'total_sales_amount', 'total_sales_quantity', 'sales_count',
        #     'total_products', 'total_variants', 'average_sale_amount',
        #     'created_at'
        # ]

        fields = [
            'id', 'name', 'owner', 'phone', 'email', 'address', 'latitude', 'longitude','total_sales_amount', 'total_sales_quantity', 'sales_count',
            'total_products', 'total_variants', 'average_sale_amount','vendor_name',
            'district', 'region', 'commune', 'type', 'status', 'registration_date',
            'turnover', 'monthly_orders', 'evaluation_score', 'created_at', 'updated_at', 'user','avatar','brander','marque_brander'
        ]
    
    def get_average_sale_amount(self, obj):
        if obj.sales_count > 0:
            return obj.total_sales_amount / obj.sales_count
        return 0