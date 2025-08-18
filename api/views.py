from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import (
    Category, Supplier, PointOfSale, Permission, Role, UserProfile,
    Product, ProductVariant, StockMovement, Order, OrderItem, Dispute, 
    Token, TokenTransaction, Notification,ProductFormat
)
from .serializers import (
    CategorySerializer, SupplierSerializer, PointOfSaleSerializer,
    PermissionSerializer, RoleSerializer, UserProfileSerializer,
    ProductSerializer, ProductVariantSerializer, StockMovementSerializer, 
    OrderSerializer, OrderItemSerializer, DisputeSerializer, 
    TokenSerializer, TokenTransactionSerializer,
    NotificationSerializer, DashboardSerializer, StockOverviewSerializer,
    ProductFormatSerializer
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


# Views existantes (inchangées sauf indication)
class OrderItemListCreateView(generics.ListCreateAPIView):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class OrderItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# Views existantes (inchangées sauf indication)
class ProductFormatListCreateView(generics.ListCreateAPIView):
    queryset = ProductFormat.objects.all()
    serializer_class = ProductFormatSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['name']

class ProductFormatDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductFormat.objects.all()
    serializer_class = ProductFormatSerializer
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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = {
        'role': ['exact'],
        'status': ['exact'],
        'points_of_sale': ['exact'],
        'establishment_type': ['exact'],
        'establishment_registration_date': ['gte', 'lte'],
    }
    search_fields = [
        'user__username', 
        'user__email', 
        'phone',
        'establishment_name',
        'establishment_address'
    ]

    def get_queryset(self):
        user_profile = self.request.user.profile
        queryset = UserProfile.objects.filter(
            points_of_sale__in=user_profile.points_of_sale.all(),
            establishment_name=user_profile.establishment_name
        ).select_related(
            'user', 'role'
        ).prefetch_related(
            'points_of_sale'
        ).distinct()
        
        return queryset

    def perform_create(self, serializer):
        if serializer.is_valid():
            # On force l'établissement à être le même que celui de l'utilisateur connecté
            serializer.validated_data['establishment_name'] = self.request.user.profile.establishment_name
            profile = serializer.save()
            
            # On lie automatiquement les POS de l'utilisateur connecté
            if not profile.points_of_sale.exists():
                profile.points_of_sale.set(self.request.user.profile.points_of_sale.all())

class UserProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_profile = self.request.user.profile
        return UserProfile.objects.filter(
            points_of_sale__in=user_profile.points_of_sale.all(),
            establishment_name=user_profile.establishment_name
        ).select_related(
            'user', 'role'
        ).prefetch_related(
            'points_of_sale'
        )

    def perform_update(self, serializer):
        # On empêche la modification de l'établissement
        if 'establishment_name' in serializer.validated_data:
            serializer.validated_data.pop('establishment_name')
            
        instance = serializer.save()
        
        # Mise à jour automatique du POS principal si nécessaire
        if (instance.points_of_sale.count() == 1 and 
            instance.establishment_name and 
            instance.establishment_name != instance.points_of_sale.first().name):
            pos = instance.points_of_sale.first()
            pos.name = instance.establishment_name
            pos.phone = instance.establishment_phone
            pos.email = instance.establishment_email
            pos.address = instance.establishment_address
            pos.type = instance.establishment_type
            pos.save()

class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['name', 'sku']

    def get_queryset(self):
        # Récupérer les POS de l'utilisateur connecté
        user_pos = self.request.user.profile.points_of_sale.all()
        return Product.objects.filter(
            point_of_sale__in=user_pos
        ).select_related('category', 'supplier', 'point_of_sale')

    def perform_create(self, serializer):
        # Get the PointOfSale instance directly from validated_data
        point_of_sale = serializer.validated_data.get('point_of_sale')
        
        if point_of_sale:
            user_pos_ids = [pos.id for pos in self.request.user.profile.points_of_sale.all()]
            if point_of_sale.id not in user_pos_ids:
                raise serializers.ValidationError(
                    {"point_of_sale": "Vous n'avez pas accès à ce point de vente"}
                )
        serializer.save()

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'id'

    def get_queryset(self):
        # Récupérer les POS de l'utilisateur connecté
        user_pos = self.request.user.profile.points_of_sale.all()
        return Product.objects.filter(
            point_of_sale__in=user_pos
        ).select_related('category', 'supplier', 'point_of_sale')

    def perform_update(self, serializer):
        # Vérifier que le nouveau POS fait partie de ceux de l'utilisateur
        point_of_sale_id = serializer.validated_data.get('point_of_sale', {}).get('id')
        if point_of_sale_id:
            user_pos_ids = [str(pos.id) for pos in self.request.user.profile.points_of_sale.all()]
            if str(point_of_sale_id) not in user_pos_ids:
                raise serializers.ValidationError(
                    {"point_of_sale": "Vous n'avez pas accès à ce point de vente"}
                )
        serializer.save()

class StockMovementListCreateView(generics.ListCreateAPIView):
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

    def get_queryset(self):
        # Récupérer les POS de l'utilisateur connecté
        user_pos = self.request.user.profile.points_of_sale.all()
        return StockMovement.objects.filter(
            product_variant__product__point_of_sale__in=user_pos
        ).select_related('product_variant__product', 'user').order_by('-date')

    def perform_create(self, serializer):
        # Vérifier que le produit fait partie d'un POS accessible
        product_variant = serializer.validated_data.get('product_variant')
        user_pos_ids = [str(pos.id) for pos in self.request.user.profile.points_of_sale.all()]
        
        if str(product_variant.product.point_of_sale.id) not in user_pos_ids:
            raise serializers.ValidationError(
                {"product_variant": "Vous n'avez pas accès à ce produit"}
            )
        
        serializer.save(user=self.request.user)

class StockMovementDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        # Récupérer les POS de l'utilisateur connecté
        user_pos = self.request.user.profile.points_of_sale.all()
        return StockMovement.objects.filter(
            product_variant__product__point_of_sale__in=user_pos
        ).select_related('product_variant__product', 'user')

    def perform_update(self, serializer):
        # Vérifier que le nouveau produit fait partie d'un POS accessible
        product_variant = serializer.validated_data.get('product_variant')
        if product_variant:
            user_pos_ids = [str(pos.id) for pos in self.request.user.profile.points_of_sale.all()]
            if str(product_variant.product.point_of_sale.id) not in user_pos_ids:
                raise serializers.ValidationError(
                    {"product_variant": "Vous n'avez pas accès à ce produit"}
                )
        serializer.save(user=self.request.user)

class ProductVariantListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['format']
    search_fields = ['barcode']

    def get_queryset(self):
        # Récupérer les POS de l'utilisateur connecté
        user_pos = self.request.user.profile.points_of_sale.all()
        return ProductVariant.objects.filter(
            product__point_of_sale__in=user_pos
        ).select_related('product', 'format')

    def perform_create(self, serializer):
        # Vérifier que le produit parent fait partie d'un POS accessible
        product = serializer.validated_data.get('product')
        user_pos_ids = [str(pos.id) for pos in self.request.user.profile.points_of_sale.all()]
        
        if str(product.point_of_sale.id) not in user_pos_ids:
            raise serializers.ValidationError(
                {"product": "Vous n'avez pas accès à ce produit"}
            )
        
        serializer.save()

class ProductVariantDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'id'

    def get_queryset(self):
        # Récupérer les POS de l'utilisateur connecté
        user_pos = self.request.user.profile.points_of_sale.all()
        return ProductVariant.objects.filter(
            product__point_of_sale__in=user_pos
        ).select_related('product', 'format')

    def perform_update(self, serializer):
        # Vérifier que le nouveau produit parent fait partie d'un POS accessible
        product = serializer.validated_data.get('product')
        if product:
            user_pos_ids = [str(pos.id) for pos in self.request.user.profile.points_of_sale.all()]
            if str(product.point_of_sale.id) not in user_pos_ids:
                raise serializers.ValidationError(
                    {"product": "Vous n'avez pas accès à ce produit"}
                )
        serializer.save()

class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status', 'priority']
    search_fields = ['customer_name', 'customer_email']

    def get_queryset(self):
        # Récupérer les POS de l'utilisateur connecté
        user_pos = self.request.user.profile.points_of_sale.all()
        return Order.objects.filter(
            point_of_sale__in=user_pos
        ).select_related('point_of_sale').prefetch_related('items')

    def perform_create(self, serializer):
        # Récupérer le point de vente depuis les données validées
        point_of_sale = serializer.validated_data.get('point_of_sale')
        
        # Si point_of_sale est fourni (cas où vous voulez le surcharger)
        if point_of_sale:
            # Vérifier que l'utilisateur a accès à ce POS
            if not self.request.user.profile.points_of_sale.filter(id=point_of_sale.id).exists():
                raise serializers.ValidationError(
                    {"point_of_sale": "Vous n'avez pas accès à ce point de vente"}
                )
        else:
            # Sinon, déterminer le POS automatiquement à partir des articles
            items_data = serializer.validated_data.get('items', [])
            if items_data:
                first_item = items_data[0]
                point_of_sale = first_item['product_variant'].product.point_of_sale
                serializer.validated_data['point_of_sale'] = point_of_sale
        
        serializer.save()

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        # Récupérer les POS de l'utilisateur connecté
        user_pos = self.request.user.profile.points_of_sale.all()
        return Order.objects.filter(
            point_of_sale__in=user_pos
        ).select_related('point_of_sale')

    def perform_update(self, serializer):
        # Vérifier que le nouveau POS fait partie de ceux de l'utilisateur
        point_of_sale_id = serializer.validated_data.get('point_of_sale', {}).get('id')
        if point_of_sale_id:
            user_pos_ids = [str(pos.id) for pos in self.request.user.profile.points_of_sale.all()]
            if str(point_of_sale_id) not in user_pos_ids:
                raise serializers.ValidationError(
                    {"point_of_sale": "Vous n'avez pas accès à ce point de vente"}
                )
        serializer.save()

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
from rest_framework import permissions, status
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Q
from django.db.models.functions import Coalesce
from decimal import Decimal
from .models import PointOfSale, Order, UserProfile, ProductVariant, StockMovement, Notification, Product
from .serializers import DashboardSerializer, StockOverviewSerializer, ProductSerializer, SimpleProductSerializer
from django.utils import timezone
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from decimal import Decimal
from datetime import timedelta
from .models import UserProfile, Order, StockMovement, Notification, PointOfSale
from .serializers import DashboardSerializer

class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # Get POS associated with the user
            user_profile = UserProfile.objects.get(user=request.user)
            user_pos = user_profile.points_of_sale.all()
            if not user_pos.exists():
                return Response(
                    {"error": "Aucun point de vente associé à cet utilisateur"},
                    status=status.HTTP_403_FORBIDDEN
                )

            today = timezone.now().date()
            yesterday = today - timedelta(days=1)
            this_month = today.replace(day=1)
            last_month = (this_month - timedelta(days=1)).replace(day=1)

            # Cumulative data (across all user's POS)
            pos_count = user_pos.count()
            pos_count_yesterday = user_pos.filter(created_at__date__lte=yesterday).count()
            pos_change = (
                f"+{((pos_count - pos_count_yesterday) / pos_count_yesterday * 100):.1f}%"
                if pos_count_yesterday > 0 else "0%"
            )

            orders_today = Order.objects.filter(point_of_sale__in=user_pos, date=today).count()
            orders_yesterday = Order.objects.filter(point_of_sale__in=user_pos, date=yesterday).count()
            orders_change = (
                f"+{((orders_today - orders_yesterday) / orders_yesterday * 100):.1f}%"
                if orders_yesterday > 0 else "0%"
            )

            revenue_this_month = Order.objects.filter(
                point_of_sale__in=user_pos, date__gte=this_month
            ).aggregate(total=Coalesce(Sum('total'), Decimal('0')))['total']
            revenue_last_month = Order.objects.filter(
                point_of_sale__in=user_pos, date__gte=last_month, date__lt=this_month
            ).aggregate(total=Coalesce(Sum('total'), Decimal('0')))['total']
            revenue_change = (
                f"+{((revenue_this_month - revenue_last_month) / revenue_last_month * 100):.1f}%"
                if revenue_last_month > 0 else "0%"
            )

            active_users = UserProfile.objects.filter(
                status='active', points_of_sale__in=user_pos
            ).distinct().count()
            active_users_yesterday = UserProfile.objects.filter(
                status='active', points_of_sale__in=user_pos, last_login__date__lte=yesterday
            ).distinct().count()
            users_change = (
                f"+{((active_users - active_users_yesterday) / active_users_yesterday * 100):.1f}%"
                if active_users_yesterday > 0 else "0%"
            )

            recent_movements = StockMovement.objects.filter(
                product_variant__product__point_of_sale__in=user_pos
            ).select_related('product_variant__product', 'user').order_by('-created_at')[:5]
            recent_orders = Order.objects.filter(
                point_of_sale__in=user_pos
            ).select_related('point_of_sale').order_by('-created_at')[:5]

            cumulative_activities = []
            for movement in recent_movements:
                cumulative_activities.append({
                    'action': f"{movement.type.capitalize()} de stock pour {movement.product_variant.product.name}",
                    'user': movement.user.username if movement.user else 'Système',
                    'time': (timezone.now() - movement.created_at).total_seconds() // 60,
                    'icon': 'Package',
                    'color': 'bg-orange-100'
                })
            for order in recent_orders:
                cumulative_activities.append({
                    'action': f"Commande {order.id} créée",
                    'user': order.customer.user.username if order.customer and order.customer.user else 'Unknown',
                    'time': (timezone.now() - order.created_at).total_seconds() // 60,
                    'icon': 'ShoppingCart',
                    'color': 'bg-purple-100'
                })
            cumulative_activities = sorted(cumulative_activities, key=lambda x: x['time'])[:5]
            cumulative_activities = [
                {**activity, 'time': self.format_time_ago(activity['time'])}
                for activity in cumulative_activities
            ]

            notifications = Notification.objects.filter(
                is_read=False,
                user=request.user,
                related_order__point_of_sale__in=user_pos
            ).filter(
                Q(related_product__point_of_sale__in=user_pos) | Q(related_product__isnull=True)
            ).select_related('related_order', 'related_product').order_by('-created_at')[:5]

            cumulative_alerts = []
            for notification in notifications:
                priority = (
                    'high' if notification.type in ['stock_alert', 'dispute'] else
                    'medium' if notification.type in ['order_update', 'promotion'] else
                    'low'
                )
                icon = (
                    'Package' if notification.type == 'stock_alert' else
                    'ShoppingCart' if notification.type == 'order_update' else
                    'AlertTriangle' if notification.type == 'dispute' else
                    'Bell'
                )
                cumulative_alerts.append({
                    'type': dict(notification.TYPE_CHOICES).get(notification.type, notification.type),
                    'message': notification.message,
                    'priority': priority,
                    'icon': icon
                })

            cumulative = {
                'pos_id': None,  # Nullable for cumulative
                'pos_name': 'Total Général',
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
                'recent_activities': cumulative_activities,
                'alerts': cumulative_alerts
            }

            # Per-POS data
            pos_data = []
            for pos in user_pos:
                pos_count = 1
                pos_count_yesterday = 1 if pos.created_at.date() <= yesterday else 0
                pos_change = (
                    f"+{((pos_count - pos_count_yesterday) / pos_count_yesterday * 100):.1f}%"
                    if pos_count_yesterday > 0 else "0%"
                )

                orders_today = Order.objects.filter(point_of_sale=pos, date=today).count()
                orders_yesterday = Order.objects.filter(point_of_sale=pos, date=yesterday).count()
                orders_change = (
                    f"+{((orders_today - orders_yesterday) / orders_yesterday * 100):.1f}%"
                    if orders_yesterday > 0 else "0%"
                )

                revenue_this_month = Order.objects.filter(
                    point_of_sale=pos, date__gte=this_month
                ).aggregate(total=Coalesce(Sum('total'), Decimal('0')))['total']
                revenue_last_month = Order.objects.filter(
                    point_of_sale=pos, date__gte=last_month, date__lt=this_month
                ).aggregate(total=Coalesce(Sum('total'), Decimal('0')))['total']
                revenue_change = (
                    f"+{((revenue_this_month - revenue_last_month) / revenue_last_month * 100):.1f}%"
                    if revenue_last_month > 0 else "0%"
                )

                active_users = UserProfile.objects.filter(
                    status='active', points_of_sale=pos
                ).distinct().count()
                active_users_yesterday = UserProfile.objects.filter(
                    status='active', points_of_sale=pos, last_login__date__lte=yesterday
                ).distinct().count()
                users_change = (
                    f"+{((active_users - active_users_yesterday) / active_users_yesterday * 100):.1f}%"
                    if active_users_yesterday > 0 else "0%"
                )

                recent_movements = StockMovement.objects.filter(
                    product_variant__product__point_of_sale=pos
                ).select_related('product_variant__product', 'user').order_by('-created_at')[:5]
                recent_orders = Order.objects.filter(
                    point_of_sale=pos
                ).select_related('point_of_sale').order_by('-created_at')[:5]

                recent_activities = []
                for movement in recent_movements:
                    recent_activities.append({
                        'action': f"{movement.type.capitalize()} de stock pour {movement.product_variant.product.name}",
                        'user': movement.user.username if movement.user else 'Système',
                        'time': (timezone.now() - movement.created_at).total_seconds() // 60,
                        'icon': 'Package',
                        'color': 'bg-orange-100'
                    })
                for order in recent_orders:
                    recent_activities.append({
                        'action': f"Commande {order.id} créée",
                        'user': order.customer.user.username if order.customer and order.customer.user else 'Unknown',
                        'time': (timezone.now() - order.created_at).total_seconds() // 60,
                        'icon': 'ShoppingCart',
                        'color': 'bg-purple-100'
                    })
                recent_activities = sorted(recent_activities, key=lambda x: x['time'])[:5]
                recent_activities = [
                    {**activity, 'time': self.format_time_ago(activity['time'])}
                    for activity in recent_activities
                ]

                notifications = Notification.objects.filter(
                    is_read=False,
                    user=request.user,
                    related_order__point_of_sale=pos
                ).filter(
                    Q(related_product__point_of_sale=pos) | Q(related_product__isnull=True)
                ).select_related('related_order', 'related_product').order_by('-created_at')[:5]

                alerts = []
                for notification in notifications:
                    priority = (
                        'high' if notification.type in ['stock_alert', 'dispute'] else
                        'medium' if notification.type in ['order_update', 'promotion'] else
                        'low'
                    )
                    icon = (
                        'Package' if notification.type == 'stock_alert' else
                        'ShoppingCart' if notification.type == 'order_update' else
                        'AlertTriangle' if notification.type == 'dispute' else
                        'Bell'
                    )
                    alerts.append({
                        'type': dict(notification.TYPE_CHOICES).get(notification.type, notification.type),
                        'message': notification.message,
                        'priority': priority,
                        'icon': icon
                    })

                pos_data.append({
                    'pos_id': str(pos.id),
                    'pos_name': pos.name,
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
                })

            # Structure data
            data = {
                'cumulative': cumulative,
                'pos_data': pos_data
            }

            # Initialize and validate serializer
            serializer = DashboardSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Profil utilisateur non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Erreur lors du chargement des données du tableau de bord: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            user_pos = user_profile.points_of_sale.all()

            if not user_pos.exists():
                return Response(
                    {"error": "Aucun point de vente associé à cet utilisateur"},
                    status=status.HTTP_403_FORBIDDEN
                )

            today = timezone.now().date()

            # Cumulative data
            total_products = Product.objects.filter(point_of_sale__in=user_pos).count()
            stock_value = ProductVariant.objects.filter(
                product__point_of_sale__in=user_pos
            ).aggregate(
                total=Coalesce(Sum(F('current_stock') * F('price')), Decimal('0'))
            )['total']
            alert_count = ProductVariant.objects.filter(
                Q(current_stock=0) | Q(current_stock__lte=F('min_stock')),
                product__point_of_sale__in=user_pos
            ).count()
            today_movements = StockMovement.objects.filter(
                product_variant__product__point_of_sale__in=user_pos,
                date__date=today
            ).count()
            critical_variants = ProductVariant.objects.filter(
                Q(current_stock=0) | Q(current_stock__lte=F('min_stock')),
                product__point_of_sale__in=user_pos
            ).select_related('product').order_by('current_stock')[:5]

            cumulative = {
                'pos_id': None,
                'pos_name': 'Total Général',
                'total_products': total_products,
                'stock_value': float(stock_value or 0),
                'alert_count': alert_count,
                'today_movements': today_movements,
                'critical_products': SimpleProductSerializer(
                    [v.product for v in critical_variants],
                    many=True
                ).data
            }

            # Per POS
            pos_data = []
            for pos in user_pos:
                total_products = Product.objects.filter(point_of_sale=pos).count()
                stock_value = ProductVariant.objects.filter(
                    product__point_of_sale=pos
                ).aggregate(
                    total=Coalesce(Sum(F('current_stock') * F('price')), Decimal('0'))
                )['total']
                alert_count = ProductVariant.objects.filter(
                    Q(current_stock=0) | Q(current_stock__lte=F('min_stock')),
                    product__point_of_sale=pos
                ).count()
                today_movements = StockMovement.objects.filter(
                    product_variant__product__point_of_sale=pos,
                    date__date=today
                ).count()
                critical_variants = ProductVariant.objects.filter(
                    Q(current_stock=0) | Q(current_stock__lte=F('min_stock')),
                    product__point_of_sale=pos
                ).select_related('product').order_by('current_stock')[:5]

                pos_data.append({
                    'pos_id': str(pos.id),
                    'pos_name': pos.name,
                    'total_products': total_products,
                    'stock_value': float(stock_value or 0),
                    'alert_count': alert_count,
                    'today_movements': today_movements,
                    'critical_products': SimpleProductSerializer(
                        [v.product for v in critical_variants],
                        many=True
                    ).data
                })

            data = {
                'cumulative': cumulative,
                'pos_data': pos_data
            }

            serializer = StockOverviewSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Profil utilisateur non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Erreur lors du chargement des données de stock: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import MobileVendor, VendorActivity, VendorPerformance
from .serializers import (
    MobileVendorSerializer,
    VendorActivitySerializer,
    VendorPerformanceSerializer,
    MobileVendorDetailSerializer
)

class MobileVendorViewSet(viewsets.ModelViewSet):
    queryset = MobileVendor.objects.select_related('point_of_sale').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'point_of_sale', 'vehicle_type', 'is_approved']
    search_fields = ['first_name', 'last_name', 'phone', 'email']
    ordering_fields = ['performance', 'date_joined', 'last_name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MobileVendorDetailSerializer
        return MobileVendorSerializer

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        vendor = self.get_object()
        stats = {
            'total_sales': vendor.average_daily_sales * 30,  # Estimation mensuelle
            'active_days': VendorActivity.objects.filter(
                vendor=vendor,
                activity_type__in=['check_in', 'sale']
            ).dates('timestamp', 'day').distinct().count(),
            'current_performance': vendor.performance,
            'last_month_performance': VendorPerformance.objects.filter(
                vendor=vendor
            ).order_by('-month').first().performance_score if VendorPerformance.objects.filter(vendor=vendor).exists() else 0
        }
        return Response(stats)

    @action(detail=False, methods=['get'])
    def by_pos(self, request):
        pos_id = request.query_params.get('pos_id')
        if not pos_id:
            return Response(
                {"error": "Le paramètre pos_id est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        vendors = MobileVendor.objects.filter(point_of_sale_id=pos_id)
        serializer = self.get_serializer(vendors, many=True)
        return Response(serializer.data)

class VendorActivityViewSet(viewsets.ModelViewSet):
    queryset = VendorActivity.objects.select_related('vendor', 'related_order').prefetch_related('related_items').all()
    serializer_class = VendorActivitySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['vendor', 'activity_type', 'related_order']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def perform_update(self, serializer):
        instance = serializer.save()
        if 'related_items' in self.request.data:
            instance.related_items.set(self.request.data['related_items'])

class VendorPerformanceViewSet(viewsets.ModelViewSet):
    queryset = VendorPerformance.objects.select_related('vendor').all()
    serializer_class = VendorPerformanceSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['vendor', 'month']
    ordering_fields = ['month', 'performance_score']
    ordering = ['-month']