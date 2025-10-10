# serializers.py
from rest_framework import serializers
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import *

class ReportSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    point_of_sale_name = serializers.CharField(source='point_of_sale.name', read_only=True)
    file_url = serializers.SerializerMethodField()
    period = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'id', 'title', 'report_type', 'format', 'generated_by', 'generated_by_name',
            'point_of_sale', 'point_of_sale_name', 'start_date', 'end_date', 'filters',
            'data', 'file', 'file_url', 'size', 'is_generated', 'created_at', 'period'
        ]
        read_only_fields = ['created_at', 'updated_at', 'generated_by']

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None

    def get_period(self, obj):
        return f"{obj.start_date} - {obj.end_date}"

class ReportGenerationSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=Report.REPORT_TYPES)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    point_of_sale = serializers.PrimaryKeyRelatedField(
        queryset=PointOfSale.objects.all(), 
        required=False, 
        allow_null=True
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        required=False, 
        allow_null=True
    )
    format = serializers.ChoiceField(choices=Report.FORMAT_CHOICES, default='pdf')

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("La date de début ne peut pas être après la date de fin.")
        return data

class DashboardSerializer(serializers.Serializer):
    # Statistiques générales
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_orders = serializers.IntegerField()
    total_products = serializers.IntegerField()
    total_vendors = serializers.IntegerField()
    total_points_of_sale = serializers.IntegerField()
    
    # Rapports par type
    reports_by_type = serializers.ListField()
    
    # Activité récente
    recent_activity = serializers.ListField()
    
    # Derniers rapports
    recent_reports = serializers.ListField()
    
    # Performance des points de vente
    top_points_of_sale = serializers.ListField()
    
    # Produits les plus vendus
    top_products = serializers.ListField()

class PointOfSaleReportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    owner = serializers.CharField()
    type = serializers.CharField()
    status = serializers.CharField()
    region = serializers.CharField()
    commune = serializers.CharField()
    total_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    monthly_orders = serializers.IntegerField()
    turnover = serializers.DecimalField(max_digits=15, decimal_places=2)
    evaluation_score = serializers.FloatField()

class ProductReportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    sku = serializers.CharField()
    category = serializers.CharField()
    supplier = serializers.CharField()
    point_of_sale = serializers.CharField()
    status = serializers.CharField()
    total_stock = serializers.IntegerField()
    total_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    variants_count = serializers.IntegerField()

class OrderReportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    customer = serializers.CharField()
    point_of_sale = serializers.CharField()
    status = serializers.CharField()
    total = serializers.DecimalField(max_digits=15, decimal_places=2)
    date = serializers.DateField()
    delivery_date = serializers.DateField()
    priority = serializers.CharField()
    items_count = serializers.IntegerField()

class MobileVendorReportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    point_of_sale = serializers.CharField()
    status = serializers.CharField()
    vehicle_type = serializers.CharField()
    zones = serializers.ListField()
    performance = serializers.FloatField()
    average_daily_sales = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_activities = serializers.IntegerField()

class PurchaseReportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    vendor = serializers.CharField()
    zone = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = serializers.DateTimeField()
    base = serializers.CharField()
    pushcard_type = serializers.CharField()