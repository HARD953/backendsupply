from rest_framework import serializers
from .models import (
    Category, Supplier, PointOfSale, Permission, Role, UserProfile,
    Product, ProductFormat, ProductVariant, ProductImage, StockMovement, 
    Order, OrderItem, Dispute, Token, TokenTransaction, Notification, Sale
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
            'turnover', 'monthly_orders', 'evaluation_score', 'created_at', 'updated_at', 'user','avatar'
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
        
from django.contrib.auth.hashers import make_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
            'username': {'required': True},
            'email': {'required': True}
        }

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)
    
class PointOfSaleNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointOfSale
        fields = ['id', 'name']

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from .models import UserProfile, Role, PointOfSale

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'password': {'required': True}
        }

class PointOfSaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointOfSale
        fields = ['id', 'name', 'phone', 'email', 'address', 'type', 'registration_date']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserCreateSerializer(required=True)
    points_of_sale = serializers.PrimaryKeyRelatedField(
        many=True, 
        read_only=True
    )
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    # Champs pour l'écriture
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), 
        source='role', 
        write_only=True,
        required=False,
        allow_null=True
    )
    points_of_sale_ids = serializers.PrimaryKeyRelatedField(
        queryset=PointOfSale.objects.all(),
        many=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'phone', 'location', 'role', 'join_date', 
            'last_login', 'status', 'avatar', 'points_of_sale',
            'establishment_name', 'establishment_phone', 'establishment_email',
            'establishment_address', 'establishment_type', 'establishment_registration_date',
            'owner',  # Nouveau champ
            # Champs supplémentaires
            'role_name',
            # Champs write-only
            'role_id', 'points_of_sale_ids'
        ]
        read_only_fields = ['join_date', 'last_login', 'owner']

    def create(self, validated_data):
        # Extraire les données de l'utilisateur
        user_data = validated_data.pop('user')
        
        # Vérifier que l'username n'existe pas déjà
        if User.objects.filter(username=user_data['username']).exists():
            raise serializers.ValidationError({"username": "Cet username existe déjà."})
        
        # Vérifier que l'email n'existe pas déjà
        if User.objects.filter(email=user_data['email']).exists():
            raise serializers.ValidationError({"email": "Cet email existe déjà."})
        
        # Créer le nouvel utilisateur
        password = user_data.pop('password')
        user = User.objects.create(**user_data)
        user.set_password(password)
        user.save()
        
        # Gérer les points de vente
        points_of_sale_ids = validated_data.pop('points_of_sale_ids', [])
        
        # Récupérer l'owner (utilisateur connecté) depuis le contexte
        owner = self.context['request'].user
        
        # Créer le profil utilisateur avec l'owner
        user_profile = UserProfile.objects.create(
            user=user, 
            owner=owner,  # Ici on set l'owner
            **validated_data
        )
        
        # Ajouter les points de vente
        if points_of_sale_ids:
            user_profile.points_of_sale.set(points_of_sale_ids)
        
        return user_profile

    def update(self, instance, validated_data):
        # Mettre à jour les données de l'utilisateur si fournies
        user_data = validated_data.pop('user', None)
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                if attr == 'password':
                    user.set_password(value)
                else:
                    setattr(user, attr, value)
            user.save()
        
        # Mettre à jour les points de vente
        points_of_sale_ids = validated_data.pop('points_of_sale_ids', None)
        
        # Mettre à jour le profil
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        if points_of_sale_ids is not None:
            instance.points_of_sale.set(points_of_sale_ids)
        
        return instance

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Role, PointOfSale
from django.db import IntegrityError

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'password': {'required': True}
        }

class PointOfSaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointOfSale
        fields = ['id', 'name', 'phone', 'email', 'address', 'type', 'registration_date']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserCreateSerializer(required=True)
    
    # Simplifions d'abord sans les relations complexes
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    # Champs write-only simplifiés
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), 
        source='role', 
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'phone', 'location', 'role', 'join_date', 
            'last_login', 'status', 'avatar',
            'establishment_name', 'establishment_phone', 'establishment_email',
            'establishment_address', 'establishment_type', 'establishment_registration_date',
            'owner',
            'role_name', 'role_id'
        ]
        read_only_fields = ['join_date', 'last_login', 'owner']

    def validate(self, data):
        """
        Validation personnalisée pour mieux gérer les erreurs
        """
        user_data = data.get('user', {})
        
        # Vérifier que les champs requis du user sont présents
        required_user_fields = ['username', 'email', 'password']
        for field in required_user_fields:
            if field not in user_data:
                raise serializers.ValidationError({
                    'user': {field: 'Ce champ est requis.'}
                })
        
        return data

    def create(self, validated_data):
        try:
            # Extraire les données de l'utilisateur
            user_data = validated_data.pop('user')
            
            # Créer le nouvel utilisateur
            password = user_data.pop('password')
            user = User.objects.create(**user_data)
            user.set_password(password)
            user.save()
            
            # Récupérer l'owner (utilisateur connecté) depuis le contexte
            owner = self.context['request'].user
            
            # Créer le profil utilisateur avec l'owner
            user_profile = UserProfile.objects.create(
                user=user, 
                owner=owner,
                **validated_data
            )
            
            return user_profile
            
        except IntegrityError as e:
            if 'username' in str(e).lower():
                raise serializers.ValidationError({
                    'user': {'username': 'Cet username existe déjà.'}
                })
            elif 'email' in str(e).lower():
                raise serializers.ValidationError({
                    'user': {'email': 'Cet email existe déjà.'}
                })
            else:
                raise serializers.ValidationError({
                    'detail': 'Erreur d\'intégrité lors de la création.'
                })
                
        except Exception as e:
            raise serializers.ValidationError({
                'detail': f'Erreur lors de la création: {str(e)}'
            })

    def update(self, instance, validated_data):
        # Pour l'instant, simplifions la mise à jour
        user_data = validated_data.pop('user', None)
        
        if user_data:
            user = instance.user
            password = user_data.pop('password', None)
            
            for attr, value in user_data.items():
                setattr(user, attr, value)
            
            if password:
                user.set_password(password)
            
            user.save()
        
        # Mettre à jour le profil
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
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


class SimpleProductSerializer1(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'status']

class ProductVariantSerializer(serializers.ModelSerializer):
    format = ProductFormatSerializer(read_only=True)
    format_id = serializers.PrimaryKeyRelatedField(
        # queryset=ProductFormat.objects.all(), source='format', write_only=True, allow_null=True,
        queryset=ProductFormat.objects.all(), 
        source='format', 
        write_only=True, 
        allow_null=True
    )
    product = SimpleProductSerializer1(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True,
        required=True  # Ajout de required=True pour s'assurer que product_id est toujours fourni
    )

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product', 'product_id', 'format', 'format_id', 
            'current_stock', 'min_stock', 'max_stock', 'price', 'barcode', 'image'
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
    point_of_sale_id = serializers.PrimaryKeyRelatedField(
        queryset=PointOfSale.objects.all(), source='point_of_sale', write_only=True
    )
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    # format_id = serializers.PrimaryKeyRelatedField(
    #     queryset=ProductFormat.objects.all(), source='format', write_only=True, allow_null=True
    # )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'category_id', 'sku', 'supplier', 'supplier_id',
            'point_of_sale', 'point_of_sale_id', 'description', 'status', 'main_image',
            'last_updated', 'created_at', 'variants', 'images'
        ]

class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'status']

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
        queryset=ProductVariant.objects.all(),
        source='product_variant',
        write_only=True
    )
    product_name = serializers.CharField(source='product_variant.product.name', read_only=True)
    name = serializers.CharField(required=False)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_variant', 'product_variant_id', 'product_name',
            'name', 'quantity', 'price', 'total'
        ]
        extra_kwargs = {
            'total': {'required': False},
            'price': {'required': False}
        }

    def validate(self, data):
        product_variant = data.get('product_variant')
        quantity = data.get('quantity')

        if not product_variant or not quantity:
            raise serializers.ValidationError("Product variant and quantity are required")

        # Calculate total automatically
        data['total'] = str(float(product_variant.price) * quantity)
        
        # Generate name if not provided
        if 'name' not in data or not data['name']:
            data['name'] = (
                f"{product_variant.product.name} - "
                f"{product_variant.format.name if product_variant.format else 'No format'}"
            )
        
        return data

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    point_of_sale = serializers.PrimaryKeyRelatedField(
        queryset=PointOfSale.objects.all(),
        required=False,
        allow_null=True
    )
    point_of_sale_details = PointOfSaleSerializer(
        source='point_of_sale',
        read_only=True
    )

    class Meta:
        model = Order
        fields = [
            'id','point_of_sale', 
            'point_of_sale_details', 'status', 'total', 'date', 
            'delivery_date', 'priority', 'notes', 'created_at', 
            'updated_at', 'items','customer'
        ]
        read_only_fields = ['status', 'total', 'created_at', 'updated_at','customer']

    def validate(self, data):
        items = data.get('items', [])
        if not items:
            raise serializers.ValidationError("At least one item is required")

        # Determine point_of_sale from first item if not provided
        if 'point_of_sale' not in data or not data['point_of_sale']:
            first_item = items[0]
            product_variant = first_item.get('product_variant')
            if not product_variant:
                raise serializers.ValidationError("Product variant is required in items")
            data['point_of_sale'] = product_variant.product.point_of_sale

        # Verify all items belong to the same point_of_sale
        # point_of_sale = data['point_of_sale']
        # for item in items:
        #     item_variant = item.get('product_variant')
        #     if item_variant.product.point_of_sale != point_of_sale:
        #         raise serializers.ValidationError(
        #             "All items must belong to the same point of sale"
        #         )

        # Calculate order total
        total = sum(
            float(item.get('product_variant').price) * item.get('quantity', 0)
            for item in items
        )
        data['total'] = str(total)

        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)

        for item_data in items_data:
            product_variant = item_data['product_variant']
            OrderItem.objects.create(
                order=order,
                product_variant=product_variant,
                quantity=item_data['quantity'],
                price=product_variant.price,
                total=float(product_variant.price) * item_data['quantity'],
                name=item_data.get('name', 
                    f"{product_variant.product.name} - "
                    f"{product_variant.format.name if product_variant.format else ''}"
                )
            )

        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        # Update order fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update or recreate items if provided
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                product_variant = item_data['product_variant']
                OrderItem.objects.create(
                    order=instance,
                    product_variant=product_variant,
                    quantity=item_data['quantity'],
                    price=product_variant.price,
                    total=float(product_variant.price) * item_data['quantity'],
                    name=item_data.get('name', 
                        f"{product_variant.product.name} - "
                        f"{product_variant.format.name if product_variant.format else ''}"
                    )
                )

        return instance

class DisputeSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    order_id = serializers.IntegerField(source='order.id', write_only=True, allow_null=True)
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
    token_id = serializers.IntegerField(source='token.id', write_only=True)
    order = OrderSerializer(read_only=True)
    order_id = serializers.IntegerField(source='order.id', write_only=True, allow_null=True)

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
    related_order_id = serializers.IntegerField(source='related_order.id', write_only=True, allow_null=True)
    related_product = ProductSerializer(read_only=True)
    related_product_id = serializers.IntegerField(source='related_product.id', write_only=True, allow_null=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'user_id', 'type', 'message', 'is_read',
            'related_order', 'related_order_id', 'related_product', 'related_product_id',
            'created_at'
        ]


from rest_framework import serializers

class PosDashboardSerializer(serializers.Serializer):
    pos_id = serializers.IntegerField(allow_null=True)  # Allow null for cumulative
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
    pos_id = serializers.IntegerField(allow_null=True)  # Allow null for cumulative
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
    order_items = OrderItemSerializer(source='related_order.items', many=True, read_only=True)
    total_products = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = VendorActivity
        fields = [
            'id', 'vendor', 'vendor_name', 'activity_type', 'activity_type_display',
            'timestamp', 'location', 'notes', 'related_order', 'order_items','quantity_assignes','quantity_sales',
            'total_products', 'total_amount', 'created_at'
        ]

    def get_total_products(self, obj):
        if obj.related_order:
            return sum(item.quantity for item in obj.related_order.items.all())
        return 0

    def get_total_amount(self, obj):
        if obj.related_order:
            return str(sum(item.total for item in obj.related_order.items.all()))  # Convert Decimal to string for JSON
        return "0.00"

class VendorActivitySummarySerializer(serializers.ModelSerializer):
    total_products = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = VendorActivity
        fields = ['id', 'total_products', 'total_amount']

    def get_total_products(self, obj):
        if obj.related_order:
            return sum(item.quantity for item in obj.related_order.items.all())
        return 0

    def get_total_amount(self, obj):
        if obj.related_order:
            return str(sum(item.total for item in obj.related_order.items.all()))  # Convert Decimal to string for JSON
        return "0.00"


from decimal import Decimal

class VendorActivityCumulativeSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    total_amount = serializers.CharField()

    def get_cumulative_data(self, vendor):
        activities = VendorActivity.objects.filter(vendor=vendor).select_related('related_order').prefetch_related('related_order__items')
        total_products = 0
        total_amount = Decimal('0.00')
        
        for activity in activities:
            if activity.related_order:
                total_products += sum(item.quantity for item in activity.related_order.items.all())
                total_amount += sum(item.total for item in activity.related_order.items.all())
        
        return {
            'total_products': total_products,
            'total_amount': str(total_amount)
        }
    
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

from .models import Purchase, MobileVendor

class PurchaseSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Purchase
    """
    vendor = serializers.PrimaryKeyRelatedField(queryset=MobileVendor.objects.all(),required=False)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Purchase
        fields = [
            'id', 'vendor', 'first_name', 'last_name', 'full_name', 
            'zone', 'amount', 'photo', 'purchase_date', 'base','pushcard_type','latitude','longitude','phone',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at','vendor']

    def validate(self, data):
        """
        Validation personnalisée pour s'assurer que les données sont cohérentes
        """
        if data['amount'] < 0:
            raise serializers.ValidationError({"amount": "Le montant ne peut pas être négatif."})
        return data
    

# serializers.py
from .models import Sale

class SaleSerializer(serializers.ModelSerializer):
    product_variant_name = serializers.CharField(source='product_variant.product.name', read_only=True)
    format = serializers.CharField(source='product_variant.format.name', read_only=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    vendor_name = serializers.CharField(source='vendor.full_name', read_only=True)
    
    class Meta:
        model = Sale
        fields = [
            'id', 
            'product_variant', 
            'customer', 
            'quantity', 
            'total_amount',
            'created_at',
            'updated_at',
            'vendor',
            'product_variant_name',
            'format',
            'customer_name',
            'vendor_name'
        ]
        read_only_fields = ['created_at', 'updated_at', 'vendor']


class PointOfSaleSerializers(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    orders_summary = serializers.DictField()
    orders = OrderSerializer(many=True, read_only=True)
    class Meta:
        model = PointOfSale
        fields = [
            'id', 'name', 'owner', 'phone', 'email', 'address', 'latitude', 'longitude',
            'district', 'region', 'commune', 'type', 'status', 'registration_date',
            'turnover', 'monthly_orders', 'evaluation_score', 'created_at', 'updated_at', 'user','avatar','orders_summary','orders'
        ]