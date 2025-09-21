# serializers.py
from rest_framework import serializers
from django.db.models import Sum, Count, Avg, F, Q, Value, DecimalField
from django.db.models.functions import Coalesce, TruncDate, TruncMonth, TruncYear
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    PointOfSale, Product, ProductVariant, Order, OrderItem, 
    MobileVendor, VendorActivity, Purchase, Sale, Category
)

class DateRangeSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    point_of_sale_id = serializers.IntegerField(required=False)
    vendor_id = serializers.IntegerField(required=False)
    category_id = serializers.IntegerField(required=False)
    region = serializers.CharField(required=False)
    commune = serializers.CharField(required=False)

class SalesReportSerializer(serializers.Serializer):
    period = serializers.CharField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    growth_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)

class ProductPerformanceSerializer(serializers.ModelSerializer):
    total_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    category_name = serializers.CharField(source='category.name')

    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'category_name', 'total_sold', 'total_revenue']

class VendorPerformanceSerializer(serializers.ModelSerializer):
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_daily_sales = serializers.DecimalField(max_digits=10, decimal_places=2)
    performance_score = serializers.FloatField()
    point_of_sale_name = serializers.CharField(source='point_of_sale.name')
    total_activities = serializers.IntegerField()
    completed_activities = serializers.IntegerField()

    class Meta:
        model = MobileVendor
        fields = [
            'id', 'first_name', 'last_name', 'phone', 'point_of_sale_name',
            'total_sales', 'total_orders', 'average_daily_sales', 
            'performance_score', 'total_activities', 'completed_activities',
            'status', 'vehicle_type'
        ]

class POSPerformanceSerializer(serializers.ModelSerializer):
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    growth_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    top_product = serializers.CharField()
    total_vendors = serializers.IntegerField()
    active_vendors = serializers.IntegerField()

    class Meta:
        model = PointOfSale
        fields = [
            'id', 'name', 'type', 'region', 'commune', 'total_sales', 
            'total_orders', 'average_order_value', 'growth_percentage', 
            'top_product', 'total_vendors', 'active_vendors'
        ]

class CategorySalesSerializer(serializers.ModelSerializer):
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_units = serializers.IntegerField()
    percentage_of_total = serializers.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        model = Category
        fields = ['id', 'name', 'total_sales', 'total_units', 'percentage_of_total']

class TimeSeriesSerializer(serializers.Serializer):
    date = serializers.DateField()
    value = serializers.DecimalField(max_digits=15, decimal_places=2)

class VendorActivitySerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.full_name')
    point_of_sale_name = serializers.CharField(source='vendor.point_of_sale.name')
    order_reference = serializers.CharField(source='related_order.id', allow_null=True)

    class Meta:
        model = VendorActivity
        fields = [
            'id', 'vendor_name', 'point_of_sale_name', 'activity_type',
            'timestamp', 'quantity_assignes', 'quantity_sales', 
            'quantity_restante', 'order_reference', 'notes'
        ]

class PurchaseSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.full_name', allow_null=True)
    point_of_sale_name = serializers.CharField(source='vendor.point_of_sale.name', allow_null=True)

    class Meta:
        model = Purchase
        fields = [
            'id', 'first_name', 'last_name', 'vendor_name', 'point_of_sale_name',
            'zone', 'amount', 'purchase_date', 'base', 'pushcard_type',
            'latitude', 'longitude', 'phone'
        ]

class VendorGeoSerializer(serializers.ModelSerializer):
    point_of_sale_name = serializers.CharField(source='point_of_sale.name')
    point_of_sale_region = serializers.CharField(source='point_of_sale.region')
    point_of_sale_commune = serializers.CharField(source='point_of_sale.commune')
    last_activity = serializers.DateTimeField(source='activities.last().timestamp', allow_null=True)
    total_sales_today = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = MobileVendor
        fields = [
            'id', 'first_name', 'last_name', 'phone', 'point_of_sale_name',
            'point_of_sale_region', 'point_of_sale_commune', 'vehicle_type',
            'status', 'last_activity', 'total_sales_today', 'latitude', 'longitude'
        ]