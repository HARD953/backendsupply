from rest_framework import serializers
from .models import (
    Category, Supplier, PointOfSale, Permission, Role, UserProfile,
    Product, ProductFormat, ProductVariant, ProductImage, StockMovement, 
    Order, OrderItem, Dispute, Token, TokenTransaction, Notification
)
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from datetime import datetime, timedelta
from django.utils import timezone

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image']

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'contact', 'address', 'email', 'logo', 'created_at']

class PointOfSaleSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = PointOfSale
        fields = [
            'id', 'name', 'owner', 'phone', 'email', 'address', 'latitude', 'longitude',
            'district', 'region', 'commune', 'type', 'status', 'registration_date',
            'turnover', 'monthly_orders', 'evaluation_score', 'created_at', 'updated_at', 'user'
        ]

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'category', 'description']

class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    users = serializers.IntegerField(source='users.count', read_only=True)

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'color', 'permissions', 'users']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
    
class PointOfSaleNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointOfSale
        fields = ['id', 'name']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), allow_null=True)
    points_of_sale = PointOfSaleNameSerializer(many=True, read_only=True)
    points_of_sale_ids = serializers.PrimaryKeyRelatedField(
        queryset=PointOfSale.objects.all(),
        source='points_of_sale',
        many=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = UserProfile
        fields = [
            'user', 'phone', 'location', 'role', 'join_date', 'last_login', 
            'status', 'avatar', 'points_of_sale', 'points_of_sale_ids',
            'establishment_name', 'establishment_phone', 'establishment_email',
            'establishment_address', 'establishment_type', 'establishment_registration_date'
        ]
        extra_kwargs = {
            'join_date': {'read_only': True},
            'establishment_registration_date': {'read_only': True},
        }

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        avatar = validated_data.pop('avatar', None)
        points_of_sale = validated_data.pop('points_of_sale', [])
        
        user = UserSerializer().create(user_data)
        profile = UserProfile.objects.create(user=user, avatar=avatar, **validated_data)
        
        if points_of_sale:
            profile.points_of_sale.set(points_of_sale)
        
        return profile

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        avatar = validated_data.pop('avatar', None)
        points_of_sale = validated_data.pop('points_of_sale', None)

        if user_data:
            user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
            if user_serializer.is_valid():
                user_serializer.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if avatar:
            instance.avatar = avatar
        
        if points_of_sale is not None:
            instance.points_of_sale.set(points_of_sale)
        
        instance.save()
        return instance

# class UserProfileSerializer(serializers.ModelSerializer):
#     role = RoleSerializer(read_only=True)
#     username = serializers.CharField(source='user.username', read_only=True)
#     email = serializers.EmailField(source='user.email', read_only=True)

#     class Meta:
#         model = UserProfile
#         fields = [
#             'id', 'username', 'email', 'phone', 'location', 'role',
#             'join_date', 'last_login', 'status', 'avatar'
#         ]

class ProductFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductFormat
        fields = ['id', 'name', 'description']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'caption', 'is_featured', 'order']

class ProductVariantSerializer(serializers.ModelSerializer):
    format = ProductFormatSerializer(read_only=True)
    format_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductFormat.objects.all(), source='format', write_only=True, allow_null=True
    )
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'format', 'format_id', 'current_stock', 'min_stock', 
            'max_stock', 'price', 'barcode', 'image'
        ]

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(), source='supplier', write_only=True
    )
    point_of_sale = PointOfSaleSerializer(read_only=True)
    point_of_sale_id = serializers.UUIDField(source='point_of_sale.id', write_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'category_id', 'sku', 'supplier', 'supplier_id',
            'point_of_sale', 'point_of_sale_id', 'description', 'status', 'main_image',
            'last_updated', 'created_at', 'variants', 'images'
        ]

class StockMovementSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantSerializer(read_only=True)
    product_variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), source='product_variant', write_only=True
    )
    product_name = serializers.CharField(source='product_variant.product.name', read_only=True)
    user = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True, allow_null=True
    )

    class Meta:
        model = StockMovement
        fields = [
            'id', 'product_variant', 'product_variant_id', 'product_name',
            'type', 'quantity', 'date', 'reason', 'user', 'user_id', 'created_at'
        ]

class OrderItemSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantSerializer(read_only=True)
    product_variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), source='product_variant', write_only=True, allow_null=True
    )
    product_name = serializers.CharField(source='product_variant.product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_variant', 'product_variant_id', 'product_name',
            'name', 'quantity', 'price', 'total'
        ]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    point_of_sale = PointOfSaleSerializer(read_only=True)
    point_of_sale_id = serializers.UUIDField(source='point_of_sale.id', write_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'customer_name', 'customer_email', 'customer_phone',
            'customer_address', 'point_of_sale', 'point_of_sale_id',
            'status', 'total', 'date', 'delivery_date', 'priority',
            'notes', 'created_at', 'updated_at', 'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data:
            instance.items.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)
        return instance

class DisputeSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    order_id = serializers.CharField(source='order.id', write_only=True, allow_null=True)
    complainant = serializers.CharField(source='complainant.username', read_only=True)
    complainant_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='complainant', write_only=True, allow_null=True
    )

    class Meta:
        model = Dispute
        fields = [
            'id', 'order', 'order_id', 'complainant', 'complainant_id',
            'description', 'status', 'resolution_details', 'created_at', 'updated_at'
        ]

class TokenSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = Token
        fields = ['id', 'user', 'user_id', 'balance', 'created_at', 'updated_at']

class TokenTransactionSerializer(serializers.ModelSerializer):
    token = TokenSerializer(read_only=True)
    token_id = serializers.UUIDField(source='token.id', write_only=True)
    order = OrderSerializer(read_only=True)
    order_id = serializers.CharField(source='order.id', write_only=True, allow_null=True)

    class Meta:
        model = TokenTransaction
        fields = [
            'id', 'token', 'token_id', 'type', 'amount', 'order', 'order_id',
            'description', 'created_at'
        ]

class NotificationSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )
    related_order = OrderSerializer(read_only=True)
    related_order_id = serializers.CharField(source='related_order.id', write_only=True, allow_null=True)
    related_product = ProductSerializer(read_only=True)
    related_product_id = serializers.UUIDField(source='related_product.id', write_only=True, allow_null=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'user_id', 'type', 'message', 'is_read',
            'related_order', 'related_order_id', 'related_product', 'related_product_id',
            'created_at'
        ]

from rest_framework import serializers

class PosDashboardSerializer(serializers.Serializer):
    pos_id = serializers.UUIDField(allow_null=True)  # Allow null for cumulative
    pos_name = serializers.CharField()
    stats = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(allow_blank=True)
        )
    )
    recent_activities = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(allow_blank=True)
        )
    )
    alerts = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(allow_blank=True)
        )
    )

class DashboardSerializer(serializers.Serializer):
    cumulative = PosDashboardSerializer()
    pos_data = serializers.ListField(child=PosDashboardSerializer())

class PosStockOverviewSerializer(serializers.Serializer):
    pos_id = serializers.UUIDField(allow_null=True)  # Allow null for cumulative
    pos_name = serializers.CharField()
    total_products = serializers.IntegerField()
    stock_value = serializers.FloatField()
    alert_count = serializers.IntegerField()
    today_movements = serializers.IntegerField()
    critical_products = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(allow_blank=True)
        )
    )

class StockOverviewSerializer(serializers.Serializer):
    cumulative = PosStockOverviewSerializer()
    pos_data = serializers.ListField(child=PosStockOverviewSerializer())



from .models import MobileVendor, VendorActivity, VendorPerformance
from .models import PointOfSale

class MobileVendorSerializer(serializers.ModelSerializer):
    point_of_sale_name = serializers.CharField(source='point_of_sale.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    vehicle_type_display = serializers.CharField(source='get_vehicle_type_display', read_only=True)
    full_name = serializers.SerializerMethodField()

    # ✅ Corriger ici
    zones = serializers.ListField(
        child=serializers.CharField(),  # ou JSONField() si c'est une liste de dicts
        allow_empty=True
    )

    class Meta:
        model = MobileVendor
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'phone', 'email', 
            'photo', 'status', 'status_display', 'vehicle_type', 'vehicle_type_display',
            'vehicle_id', 'zones', 'performance', 'average_daily_sales',
            'point_of_sale', 'point_of_sale_name', 'date_joined', 'last_activity',
            'is_approved', 'notes', 'created_at'
        ]
        extra_kwargs = {
            'point_of_sale': {'required': True},
            'phone': {'required': True}
        }

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    # Cette méthode devient redondante mais peut rester
    def validate_zones(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Les zones doivent être une liste")
        return value


class VendorActivitySerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.full_name', read_only=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    
    class Meta:
        model = VendorActivity
        fields = [
            'id', 'vendor', 'vendor_name', 'activity_type', 'activity_type_display',
            'timestamp', 'location', 'notes', 'related_order', 'created_at'
        ]

class VendorPerformanceSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.full_name', read_only=True)
    month_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorPerformance
        fields = [
            'id', 'vendor', 'vendor_name', 'month', 'month_formatted',
            'total_sales', 'orders_completed', 'days_worked',
            'distance_covered', 'performance_score', 'bonus_earned',
            'notes', 'created_at', 'updated_at'
        ]
    
    def get_month_formatted(self, obj):
        return obj.month.strftime("%B %Y")

class MobileVendorDetailSerializer(MobileVendorSerializer):
    activities = VendorActivitySerializer(many=True, read_only=True)
    performances = VendorPerformanceSerializer(many=True, read_only=True)
    
    class Meta(MobileVendorSerializer.Meta):
        fields = MobileVendorSerializer.Meta.fields + ['activities', 'performances']