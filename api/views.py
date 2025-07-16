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

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Q
from django.db.models.functions import Coalesce
from decimal import Decimal
from .models import PointOfSale, Order, User, ProductVariant, StockMovement, Notification
from .serializers import DashboardSerializer

class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        this_month = today.replace(day=1)
        last_month = (this_month - timedelta(days=1)).replace(day=1)

        # Calculate statistics for the dashboard
        # Points of Sale
        pos_count = PointOfSale.objects.count()
        pos_count_yesterday = PointOfSale.objects.filter(
            created_at__date__lte=yesterday
        ).count()
        pos_change = (
            f"+{((pos_count - pos_count_yesterday) / pos_count_yesterday * 100):.1f}%"
            if pos_count_yesterday > 0 else "0%"
        )

        # Daily Orders
        orders_today = Order.objects.filter(date=today).count()
        orders_yesterday = Order.objects.filter(date=yesterday).count()
        orders_change = (
            f"+{((orders_today - orders_yesterday) / orders_yesterday * 100):.1f}%"
            if orders_yesterday > 0 else "0%"
        )

        # Monthly Revenue
        revenue_this_month = Order.objects.filter(
            date__gte=this_month
        ).aggregate(total=Coalesce(Sum('total'), Decimal('0')))['total']
        revenue_last_month = Order.objects.filter(
            date__gte=last_month, date__lt=this_month
        ).aggregate(total=Coalesce(Sum('total'), Decimal('0')))['total']
        revenue_change = (
            f"+{((revenue_this_month - revenue_last_month) / revenue_last_month * 100):.1f}%"
            if revenue_last_month > 0 else "0%"
        )

        # Active Users
        active_users = UserProfile.objects.filter(status='active').count()
        active_users_yesterday = UserProfile.objects.filter(
            status='active', last_login__date__lte=yesterday
        ).count()
        users_change = (
            f"+{((active_users - active_users_yesterday) / active_users_yesterday * 100):.1f}%"
            if active_users_yesterday > 0 else "0%"
        )

        # Recent Activities (based on Stock Movements and Orders)
        recent_movements = StockMovement.objects.select_related(
            'product_variant__product', 'user'
        ).order_by('-created_at')[:5]
        recent_orders = Order.objects.select_related('point_of_sale').order_by('-created_at')[:5]
        
        recent_activities = []
        for movement in recent_movements:
            recent_activities.append({
                'action': f"{movement.type.capitalize()} de stock pour {movement.product_variant.product.name}",
                'user': movement.user.username if movement.user else 'Système',
                'time': (timezone.now() - movement.created_at).total_seconds() // 60,  # Time in minutes
                'icon': 'Package',
                'color': 'bg-orange-100'
            })
        for order in recent_orders:
            recent_activities.append({
                'action': f"Commande {order.id} créée",
                'user': order.customer_name,
                'time': (timezone.now() - order.created_at).total_seconds() // 60,  # Time in minutes
                'icon': 'ShoppingCart',
                'color': 'bg-purple-100'
            })
        # Sort activities by time and limit to 5
        recent_activities = sorted(recent_activities, key=lambda x: x['time'])[:5]
        recent_activities = [
            {
                **activity,
                'time': self.format_time_ago(activity['time'])
            } for activity in recent_activities
        ]

        # Alerts (based on low stock and pending disputes)
        low_stock_alerts = ProductVariant.objects.filter(
            Q(current_stock=0) | Q(current_stock__lte=F('min_stock'))
        ).select_related('product')[:3]
        pending_disputes = Dispute.objects.filter(status='en_attente')[:3]

        alerts = []
        for variant in low_stock_alerts:
            alerts.append({
                'type': 'Stock Faible',
                'message': f"Le stock de {variant.product.name} ({variant.format.name if variant.format else 'Sans format'}) est faible: {variant.current_stock} unités",
                'priority': 'high' if variant.current_stock == 0 else 'medium',
                'icon': 'Package'
            })
        for dispute in pending_disputes:
            alerts.append({
                'type': 'Contentieux',
                'message': f"Nouveau contentieux pour la commande {dispute.order.id if dispute.order else 'N/A'}",
                'priority': 'high',
                'icon': 'AlertTriangle'
            })

        # Structure data to match frontend expectations
        data = {
            'stats': [
                {
                    'title': 'Points de Vente',
                    'value': str(pos_count),
                    'change': pos_change,
                    'color': 'bg-blue-100 border-blue-200',
                    'icon': 'MapPin'
                },
                {
                    'title': 'Commandes du Jour',
                    'value': str(orders_today),
                    'change': orders_change,
                    'color': 'bg-green-100 border-green-200',
                    'icon': 'ShoppingCart'
                },
                {
                    'title': 'Revenus Mensuels',
                    'value': f"₣ {revenue_this_month:,.2f}",
                    'change': revenue_change,
                    'color': 'bg-purple-100 border-purple-200',
                    'icon': 'Coins'
                },
                {
                    'title': 'Utilisateurs Actifs',
                    'value': str(active_users),
                    'change': users_change,
                    'color': 'bg-orange-100 border-orange-200',
                    'icon': 'Users'
                }
            ],
            'recent_activities': recent_activities,
            'alerts': alerts
        }

        serializer = DashboardSerializer(data)
        return Response(serializer.data)

    def format_time_ago(self, minutes):
        if minutes < 60:
            return f"{int(minutes)} min"
        hours = minutes // 60
        if hours < 24:
            return f"{int(hours)}h"
        days = hours // 24
        return f"{int(days)}j"

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