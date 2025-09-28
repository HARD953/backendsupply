from rest_framework import serializers
from .models import MobileVendor

class MobileVendorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    point_of_sale_name = serializers.CharField(source='point_of_sale.name', read_only=True)
    
    class Meta:
        model = MobileVendor
        fields = [
            'id', 'user', 'point_of_sale', 'point_of_sale_name', 'first_name', 'last_name', 
            'full_name', 'phone', 'email', 'photo', 'status', 'vehicle_type', 'vehicle_id',
            'zones', 'performance', 'average_daily_sales', 'date_joined', 'last_activity',
            'is_approved', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['performance', 'average_daily_sales', 'last_activity']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

class VendorPerformanceSerializer(serializers.Serializer):
    vendor_id = serializers.IntegerField()
    vendor_name = serializers.CharField()
    period = serializers.CharField()
    performance_percentage = serializers.FloatField()
    statistics = serializers.DictField()

class VendorRankingSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    vendor_id = serializers.IntegerField()
    vendor_name = serializers.CharField()
    point_of_sale = serializers.CharField()
    performance_percentage = serializers.FloatField()
    total_sales = serializers.FloatField()
    sales_count = serializers.IntegerField()
    average_daily_sales = serializers.FloatField()