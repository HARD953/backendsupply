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
    class Meta:
        model = PointOfSale
        fields = [
            'id', 'name', 'owner', 'phone', 'email', 'address', 'latitude', 'longitude',
            'district', 'region', 'commune', 'type', 'status', 'registration_date',
            'turnover', 'monthly_orders', 'evaluation_score', 'created_at', 'updated_at'
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

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), allow_null=True)

    class Meta:
        model = UserProfile
        fields = ['user', 'phone', 'location', 'role', 'join_date', 'last_login', 'status', 'avatar']
        extra_kwargs = {
            'join_date': {'read_only': True},  # Rendre join_date en lecture seule
        }

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        avatar = validated_data.pop('avatar', None)
        user = UserSerializer().create(user_data)
        profile = UserProfile.objects.create(user=user, avatar=avatar, **validated_data)
        return profile

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        avatar = validated_data.pop('avatar', None)

        # Mise à jour de l'utilisateur
        if user_data:
            user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
            if user_serializer.is_valid():
                user_serializer.save()

        # Mise à jour du profil
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if avatar:
            instance.avatar = avatar
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

class DashboardSerializer(serializers.Serializer):
    stats = serializers.DictField(child=serializers.DictField())
    recent_activities = serializers.ListField(child=serializers.DictField())
    alerts = serializers.ListField(child=serializers.DictField())

class StockOverviewSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    stock_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    alert_count = serializers.IntegerField()
    today_movements = serializers.IntegerField()
    critical_products = ProductSerializer(many=True)