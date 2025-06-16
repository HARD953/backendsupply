from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import (
    Category, Supplier, PointOfSale, Permission, Role, UserProfile,
    Product, ProductVariant, StockMovement, Order, OrderItem, Dispute, 
    Token, TokenTransaction, Notification
)
from .serializers import (
    CategorySerializer, SupplierSerializer, PointOfSaleSerializer,
    PermissionSerializer, RoleSerializer, UserProfileSerializer,
    ProductSerializer, ProductVariantSerializer, StockMovementSerializer, 
    OrderSerializer, OrderItemSerializer, DisputeSerializer, 
    TokenSerializer, TokenTransactionSerializer,
    NotificationSerializer, DashboardSerializer, StockOverviewSerializer
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Sum, Q, F
from django.db.models.functions import Coalesce
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal

# Views existantes (inchangées sauf indication)
class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['name']

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class SupplierListCreateView(generics.ListCreateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['name', 'email']

class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class PointOfSaleListCreateView(generics.ListCreateAPIView):
    queryset = PointOfSale.objects.all()
    serializer_class = PointOfSaleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['type', 'status', 'district', 'region', 'commune']
    search_fields = ['name', 'owner', 'email']

class PointOfSaleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PointOfSale.objects.all()
    serializer_class = PointOfSaleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class PermissionListView(generics.ListAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class PermissionDetailView(generics.RetrieveAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class RoleListCreateView(generics.ListCreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['name']

class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class UserProfileListCreateView(generics.ListCreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['role', 'status']
    search_fields = ['user__username', 'user__email', 'phone']

class UserProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.select_related('category', 'supplier', 'point_of_sale')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category', 'point_of_sale', 'status']
    search_fields = ['name', 'sku']

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related('category', 'supplier', 'point_of_sale')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class StockMovementListCreateView(generics.ListCreateAPIView):
    queryset = StockMovement.objects.select_related(
        'product_variant__product',
        'user'
    ).order_by('-date')
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'product_variant': ['exact'],
        'type': ['exact'],
        'date': ['gte', 'lte', 'exact'],
    }
    search_fields = ['reason', 'product_variant__product__name']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class StockMovementDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = StockMovement.objects.select_related(
        'product_variant__product',
        'user'
    )
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

class ProductVariantListCreateView(generics.ListCreateAPIView):
    queryset = ProductVariant.objects.select_related('product', 'format')
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['product', 'format']
    search_fields = ['barcode']

class ProductVariantDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductVariant.objects.select_related('product', 'format')
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
class OrderListCreateView(generics.ListCreateAPIView):
    queryset = Order.objects.select_related('point_of_sale')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['point_of_sale', 'status', 'priority']
    search_fields = ['customer_name', 'customer_email']

    def perform_create(self, serializer):
        serializer.save()

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.select_related('point_of_sale')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class DisputeListCreateView(generics.ListCreateAPIView):
    queryset = Dispute.objects.select_related('order', 'complainant')
    serializer_class = DisputeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['order', 'complainant', 'status']
    search_fields = ['description']

class DisputeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Dispute.objects.select_related('order', 'complainant')
    serializer_class = DisputeSerializer
    permission_classes = [permissions.IsAuthenticated]

class TokenListCreateView(generics.ListCreateAPIView):
    queryset = Token.objects.select_related('user')
    serializer_class = TokenSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user']

class TokenDetailView(generics.RetrieveUpdateAPIView):
    queryset = Token.objects.select_related('user')
    serializer_class = TokenSerializer
    permission_classes = [permissions.IsAuthenticated]

class TokenTransactionListCreateView(generics.ListCreateAPIView):
    queryset = TokenTransaction.objects.select_related('token', 'order')
    serializer_class = TokenTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['token', 'type', 'order']
    search_fields = ['description']

class TokenTransactionDetailView(generics.RetrieveAPIView):
    queryset = TokenTransaction.objects.select_related('token', 'order')
    serializer_class = TokenTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

class NotificationListCreateView(generics.ListCreateAPIView):
    queryset = Notification.objects.select_related('user', 'related_order', 'related_product')
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['user', 'type', 'is_read']
    search_fields = ['message']

class NotificationDetailView(generics.RetrieveUpdateAPIView):
    queryset = Notification.objects.select_related('user', 'related_order', 'related_product')
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        this_month = today.replace(day=1)
        last_month = (this_month - timedelta(days=1)).replace(day=1)

        # Calcul des statistiques (adapté si nécessaire)
        pos_count = PointOfSale.objects.count()
        # ... (le reste de la méthode reste inchangé)

        serializer = DashboardSerializer(data)
        return Response(serializer.data)

class StockOverviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        
        # Total Products
        total_products = Product.objects.count()
        
        # Stock Value - maintenant calculé sur ProductVariant
        stock_value = ProductVariant.objects.aggregate(
            total=Coalesce(Sum(F('current_stock') * F('price')), Decimal('0')
        )['total'])
        
        # Alert Count - maintenant basé sur ProductVariant
        alert_count = ProductVariant.objects.filter(
            Q(current_stock=0) | Q(current_stock__lte=F('min_stock'))
        ).count()
        
        # Today's Movements
        today_movements = StockMovement.objects.filter(date__date=today).count()
        
        # Critical Products (variantes avec stock faible ou rupture)
        critical_variants = ProductVariant.objects.filter(
            Q(current_stock=0) | Q(current_stock__lte=F('min_stock'))
        ).select_related('product').order_by('current_stock')[:5]
        
        data = {
            'total_products': total_products,
            'stock_value': stock_value,
            'alert_count': alert_count,
            'today_movements': today_movements,
            'critical_products': ProductSerializer(
                [v.product for v in critical_variants], 
                many=True
            ).data
        }
        
        serializer = StockOverviewSerializer(data)
        return Response(serializer.data)