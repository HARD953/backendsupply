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
    ProductFormatSerializer,PointOfSaleSerializers
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
        # Récupérer le profil de l'utilisateur connecté comme customer
        user_profile = self.request.user.id
        
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
        
        # Sauvegarder avec le customer = profil de l'utilisateur connecté
        serializer.save(customer=user_profile)

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
    MobileVendorDetailSerializer,VendorActivitySummarySerializer
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
    queryset = VendorActivity.objects.select_related('vendor', 'related_order').prefetch_related('related_order__items', 'related_order__items__product_variant', 'related_order__items__product_variant__product').all()
    serializer_class = VendorActivitySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['vendor', 'activity_type', 'related_order']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def perform_update(self, serializer):
        instance = serializer.save()

class VendorActivitySummaryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VendorActivity.objects.select_related('related_order').prefetch_related('related_order__items').all()
    serializer_class = VendorActivitySummarySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['vendor', 'activity_type', 'related_order']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def perform_update(self, serializer):
        instance = serializer.save()

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import rest_framework.filters as filters
from .models import VendorActivity, MobileVendor
from .serializers import VendorActivitySummarySerializer, VendorActivityCumulativeSerializer
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.functions import ExtractYear, ExtractMonth  # <-- Ajoutez cette ligne

class VendorActivitySummaryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VendorActivity.objects.select_related('related_order').prefetch_related('related_order__items').all()
    serializer_class = VendorActivitySummarySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['activity_type', 'related_order']  # Remove 'vendor' from filterset_fields
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        """
        Filter activities for the connected user's MobileVendor instance.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()  # Return empty queryset for unauthenticated users

        try:
            # Assuming user has a OneToOneField to MobileVendor
            vendor = user.mobile_vendor  # Access the MobileVendor via the related_name
            return queryset.filter(vendor=vendor)
        except ObjectDoesNotExist:
            # If the user has no MobileVendor, return an empty queryset
            return queryset.none()

    @action(detail=False, methods=['get'], url_path='cumulative')
    def cumulative(self, request):
        """
        Return cumulative totals for the connected user's vendor.
        """
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Utilisateur non connecté"}, status=401)

        try:
            vendor = user.mobile_vendor
        except ObjectDoesNotExist:
            return Response({"error": "Aucun vendeur associé à cet utilisateur"}, status=400)

        serializer = VendorActivityCumulativeSerializer(data=self.get_cumulative_data(vendor))
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    def get_cumulative_data(self, vendor):
        """
        Calculate cumulative totals for the given vendor.
        """
        return VendorActivityCumulativeSerializer().get_cumulative_data(vendor)

    def perform_update(self, serializer):
        """
        Optional: If updates are needed, ensure proper validation.
        """
        instance = serializer.save()


class VendorPerformanceViewSet(viewsets.ModelViewSet):
    queryset = VendorPerformance.objects.select_related('vendor').all()
    serializer_class = VendorPerformanceSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['vendor', 'month']
    ordering_fields = ['month', 'performance_score']
    ordering = ['-month']


from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import Purchase, MobileVendor
from .serializers import PurchaseSerializer
from datetime import datetime, date, timedelta

class PurchaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur le modèle Purchase
    """
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Associe automatiquement le vendeur connecté lors de la création
        """
        try:
            # Récupère le MobileVendor associé à l'utilisateur connecté
            vendor = MobileVendor.objects.get(user=self.request.user)
        except MobileVendor.DoesNotExist:
            raise ValidationError({"detail": "Aucun vendeur ambulant associé à cet utilisateur."})
        
        serializer.save(vendor=vendor)

    def get_queryset(self):
        """
        Filtre optionnel par vendeur si 'vendor_id' est fourni dans les paramètres
        """
        queryset = super().get_queryset()
        vendor_id = self.request.query_params.get('vendor_id')
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)
        return queryset.order_by('-purchase_date')
    

# views.py
from django.shortcuts import get_object_or_404
from .models import Sale
from .serializers import SaleSerializer
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime
from rest_framework import status

class SaleViewSet(viewsets.ModelViewSet):
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retourne uniquement les ventes de l'utilisateur connecté
        """
        return Sale.objects.filter(vendor=self.request.user.id)

    def perform_create(self, serializer):
        """
        Crée une vente et met à jour le stock
        """
        # Get the MobileVendor instance from the authenticated user
        try:
            # Access the MobileVendor instance through the OneToOne relationship
            vendor_instance = self.request.user.mobile_vendor
        except AttributeError:
            # If user doesn't have mobile_vendor attribute
            raise serializers.ValidationError({"error": "Utilisateur non associé à un vendeur mobile"})
        except MobileVendor.DoesNotExist:
            # If the MobileVendor instance doesn't exist for this user
            raise serializers.ValidationError({"error": "Profil vendeur mobile non trouvé pour cet utilisateur"})
        
        # Save the sale with the MobileVendor instance
        sale = serializer.save(vendor=vendor_instance)
        
        # Mettre à jour le stock du produit
        product_variant = sale.product_variant
        if product_variant.current_stock >= sale.quantity:
            product_variant.current_stock -= sale.quantity
            product_variant.save()
        else:
            # Annuler la vente si stock insuffisant
            sale.delete()
            raise serializers.ValidationError({"error": "Stock insuffisant"})

    def perform_update(self, serializer):
        """
        Met à jour une vente et ajuste le stock
        """
        # Sauvegarder l'ancienne quantité pour ajuster le stock
        old_quantity = self.get_object().quantity
        
        # Mettre à jour la vente
        updated_sale = serializer.save()
        
        # Ajuster le stock du produit
        product_variant = updated_sale.product_variant
        
        # Calculer la différence de quantité
        quantity_diff = old_quantity - updated_sale.quantity
        
        # Mettre à jour le stock
        if quantity_diff != 0:
            product_variant.current_stock += quantity_diff
            
            # Vérifier que le stock ne devient pas négatif
            if product_variant.current_stock < 0:
                raise serializers.ValidationError(
                    {"error": "La modification entraînerait un stock négatif"}
                )
            
            product_variant.save()

    def perform_destroy(self, instance):
        """
        Supprime une vente et restaure le stock
        """
        # Restaurer le stock avant de supprimer la vente
        product_variant = instance.product_variant
        product_variant.current_stock += instance.quantity
        product_variant.save()
        
        instance.delete()

    @action(detail=False, methods=['get'], url_path='customer/(?P<customer_id>[^/.]+)')
    def by_customer(self, request, customer_id=None):
        """
        Retourne les ventes pour un client spécifique
        """
        sales = self.get_queryset().filter(customer_id=customer_id)
        serializer = self.get_serializer(sales, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='product/(?P<product_variant_id>[^/.]+)')
    def by_product(self, request, product_variant_id=None):
        """
        Retourne les ventes pour une variante de produit spécifique
        """
        sales = self.get_queryset().filter(product_variant_id=product_variant_id)
        serializer = self.get_serializer(sales, many=True)
        return Response(serializer.data)
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Retourne un résumé des ventes
        Permet de filtrer par date (format: YYYY-MM-DD) et par vendeur (vendor_id)
        Par défaut: date d'aujourd'hui et utilisateur connecté
        """
        # Récupérer l'ID du vendeur depuis les paramètres de requête
        vendor_id = request.query_params.get('vendor_id', None)
        
        # Déterminer quel vendeur utiliser
        if vendor_id:
            try:
                vendor = MobileVendor.objects.get(id=vendor_id)
                # Vérifier les permissions si nécessaire
                # if not request.user.has_perm('app.view_vendor_summary', vendor):
                #     return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
            except MobileVendor.DoesNotExist:
                return Response(
                    {"error": "Vendeur non trouvé"},
                    status=status.HTTP_404_NOT_FOUND
                )
            except ValueError:
                return Response(
                    {"error": "ID de vendeur invalide"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Utiliser l'utilisateur connecté par défaut
            vendor = self.request.user.mobile_vendor
        
        # Récupérer le queryset de base filtré par vendeur
        queryset = Sale.objects.filter(vendor=vendor)
        
        # Récupérer la date depuis les paramètres de requête
        date_param = request.query_params.get('date', None)
        
        if date_param:
            try:
                # Convertir la date string en objet date
                target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
                # Filtrer les ventes pour la date spécifiée
                queryset = queryset.filter(created_at__date=target_date)
            except ValueError:
                return Response(
                    {"error": "Format de date invalide. Utilisez YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Par défaut, utiliser la date d'aujourd'hui
            today = timezone.now().date()
            queryset = queryset.filter(created_at__date=today)
        
        # Calculer les statistiques
        total_sales = queryset.count()
        total_revenue = queryset.aggregate(total=Sum('total_amount'))['total'] or 0
        total_quantity = queryset.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Calculer le nombre de clients uniques
        unique_customers = queryset.values('customer').distinct().count()
        
        # Produits les plus vendus (top 5)
        top_products = (
            queryset.values('product_variant__product__name')
            .annotate(total_quantity=Sum('quantity'), total_revenue=Sum('total_amount'))
            .order_by('-total_quantity')[:5]
        )

        # CORRECTION: Utiliser l'objet vendor au lieu de vendor_id pour les filtres
        purchases = Purchase.objects.filter(vendor=vendor)
        sales = Sale.objects.filter(vendor=vendor)
        purchase_count = purchases.count()
        sales_count = sales.count()  # On peut réutiliser le queryset existant

        # CORRECTION: Utiliser le queryset existant au lieu de refaire le filtre
        total_amounts = sales.aggregate(total=Sum('total_amount'))['total'] or 0
        total_quantitys = sales.aggregate(total=Sum('quantity'))['total'] or 0

        # Zones les plus actives (top 3)
        top_zones = (
            purchases.values('zone')
            .annotate(count=Count('id'), revenue=Sum('amount'))
            .order_by('-count')[:3]
        )
        
        return Response({
            'date': date_param or timezone.now().date().isoformat(),
            'vendor_id': vendor.id,
            'vendor_name': vendor.full_name,
            'total_sales': total_sales,
            'total_revenue': float(total_revenue),
            'total_quantity': total_quantity,
            'unique_customers': unique_customers,
            'average_sale_amount': float(total_revenue / total_sales) if total_sales > 0 else 0,
            'top_products': list(top_products),
            'top_zones': list(top_zones),
            'purchase_count': purchase_count,
            'sales_count': sales_count,
            'total_amounts': float(total_amounts),
            'total_quantitys': total_quantitys
        })
    @action(detail=False, methods=['get'])
    def performance(self, request):
        """
        Retourne les performances mensuelles avec:
        - Nombre de clients par mois
        - Montant total vendu par mois
        - Nombre de produits vendus par mois
        - Calculs de performance mensuels
        Permet de filtrer par vendeur (vendor_id) et par période
        """
        # Récupérer l'ID du vendeur depuis les paramètres de requête
        vendor_id = request.query_params.get('vendor_id', None)
        
        # Déterminer quel vendeur utiliser
        if vendor_id:
            try:
                vendor = MobileVendor.objects.get(id=vendor_id)
            except MobileVendor.DoesNotExist:
                return Response(
                    {"error": "Vendeur non trouvé"},
                    status=status.HTTP_404_NOT_FOUND
                )
            except ValueError:
                return Response(
                    {"error": "ID de vendeur invalide"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Utiliser l'utilisateur connecté par défaut
            vendor = self.request.user.mobile_vendor
        
        # Récupérer les dates de début et fin depuis les paramètres de requête
        start_date_param = request.query_params.get('start_date')
        end_date_param = request.query_params.get('end_date')
        
        # Définir la période par défaut (6 derniers mois)
        if not start_date_param or not end_date_param:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=180)  # 6 mois
        else:
            try:
                start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {"error": "Format de date invalide. Utilisez YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Récupérer le queryset de base filtré par vendeur et période
        sales_queryset = Sale.objects.filter(
            vendor=vendor,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # Agrégation des données par mois
        monthly_data = (
            sales_queryset
            .annotate(
                year=ExtractYear('created_at'),
                month=ExtractMonth('created_at')
            )
            .values('year', 'month')
            .annotate(
                total_customers=Count('customer', distinct=True),
                total_revenue=Sum('total_amount'),
                total_products_sold=Sum('quantity'),
                total_sales=Count('id')
            )
            .order_by('year', 'month')
        )
        
        # Calcul des indicateurs de performance mensuels
        performance_data = []
        for data in monthly_data:
            month_date = date(data['year'], data['month'], 1)
            month_name = month_date.strftime('%B %Y')
            
            # Calcul de la performance (ex: ratio revenu/vente)
            performance_ratio = (
                data['total_revenue'] / data['total_sales'] 
                if data['total_sales'] > 0 else 0
            )
            
            # Calcul du panier moyen
            average_basket = (
                data['total_revenue'] / data['total_customers'] 
                if data['total_customers'] > 0 else 0
            )
            
            performance_data.append({
                'month': month_name,
                'year': data['year'],
                'month_number': data['month'],
                'total_customers': data['total_customers'],
                'total_revenue': float(data['total_revenue'] or 0),
                'total_products_sold': data['total_products_sold'] or 0,
                'total_sales': data['total_sales'],
                'performance_ratio': float(performance_ratio),
                'average_basket': float(average_basket),
                'revenue_per_customer': (
                    float(data['total_revenue'] / data['total_customers']) 
                    if data['total_customers'] > 0 else 0
                )
            })
        
        # Calcul des totaux globaux
        total_summary = {
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'total_customers': sum(item['total_customers'] for item in performance_data),
            'total_revenue': sum(item['total_revenue'] for item in performance_data),
            'total_products_sold': sum(item['total_products_sold'] for item in performance_data),
            'total_sales': sum(item['total_sales'] for item in performance_data),
            'overall_performance': (
                sum(item['total_revenue'] for item in performance_data) / 
                sum(item['total_sales'] for item in performance_data) 
                if sum(item['total_sales'] for item in performance_data) > 0 else 0
            )
        }
        
        return Response({
            'vendor_id': vendor.id,
            'vendor_name': vendor.full_name,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'monthly_performance': performance_data,
            'summary': total_summary,
            'performance_indicators': {
                'best_month': max(performance_data, key=lambda x: x['total_revenue']) if performance_data else None,
                'worst_month': min(performance_data, key=lambda x: x['total_revenue']) if performance_data else None,
                'growth_rate': self.calculate_growth_rate(performance_data) if len(performance_data) >= 2 else 0
            }
        })

    def calculate_growth_rate(self, performance_data):
        """
        Calcule le taux de croissance entre le premier et le dernier mois
        """
        if len(performance_data) < 2:
            return 0
        
        # Trier par année et mois pour être sûr de l'ordre
        sorted_data = sorted(performance_data, key=lambda x: (x['year'], x['month_number']))
        
        first_month = sorted_data[0]['total_revenue']
        last_month = sorted_data[-1]['total_revenue']
        
        if first_month == 0:
            return 0
        
        growth_rate = ((last_month - first_month) / first_month) * 100
        return float(growth_rate)
    
from django.db.models import Sum, F, Count
from django.utils import timezone
from datetime import datetime
from django.http import JsonResponse
from .models import Purchase, Sale
from django.conf import settings

def get_customer_sales(request):
    # Récupérer les dates de début et fin depuis la requête
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    # Convertir les dates en objets datetime
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else timezone.now().date() - timezone.timedelta(days=30)
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else timezone.now().date()
    
    # Ajouter le temps à la fin de la journée pour end_date
    end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
    
    # Récupérer les achats dans la période spécifiée
    purchases = Purchase.objects.filter(
        purchase_date__gte=start_date,
        purchase_date__lte=end_date
    ).prefetch_related('purchases')  # Prefetch related sales
    
    customer_data = []
    
    for purchase in purchases:
        # Récupérer toutes les ventes associées à cet achat
        sales = purchase.purchases.all()
        
        # Calculer le total des ventes pour ce client
        total_sales_amount = sales.aggregate(total=Sum('total_amount'))['total'] or 0
        total_quantity = sales.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Générer l'URL complète de la photo si elle existe
        photo_url = None
        if purchase.photo:
            photo_url = request.build_absolute_uri(purchase.photo.url)
        
        customer_data.append({
            'id': purchase.id,
            'full_name': purchase.full_name,
            'phone': purchase.phone,
            'zone': purchase.zone,
            'base': purchase.base,
            'pushcard_type': purchase.pushcard_type,
            'latitude': purchase.latitude,
            'longitude': purchase.longitude,
            'purchase_date': purchase.purchase_date.isoformat(),
            'photo_url': photo_url,  # ✅ Ajout de l'URL de la photo
            'total_sales_amount': float(total_sales_amount),
            'total_quantity': total_quantity,
            'sales_count': sales.count(),
            'sales_details': [
                {
                    'product': sale.product_variant.product.name if sale.product_variant and sale.product_variant.product else 'N/A',
                    'variant': sale.product_variant.product if sale.product_variant else 'N/A',
                    'quantity': sale.quantity,
                    'amount': float(sale.total_amount),
                    'date': sale.created_at.isoformat()
                }
                for sale in sales
            ]
        })
    
    return JsonResponse({
        'period': {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        },
        'customers': customer_data,
        'total_customers': len(customer_data),
        'grand_total_sales': sum(customer['total_sales_amount'] for customer in customer_data)
    })


def get_customer_sales_optimized(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    # Conversion des dates
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else timezone.now().date() - timezone.timedelta(days=30)
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else timezone.now().date()
    end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
    
    # Requête optimisée avec aggregation
    purchases = Purchase.objects.filter(
        purchase_date__gte=start_date,
        purchase_date__lte=end_date
    ).annotate(
        total_sales_amount=Sum('purchases__total_amount'),
        total_quantity=Sum('purchases__quantity'),
        sales_count=Count('purchases')
    ).select_related('vendor').prefetch_related('purchases__product_variant__product')
    
    customer_data = []
    
    for purchase in purchases:
        customer_data.append({
            'id': purchase.id,
            'full_name': purchase.full_name,
            'phone': purchase.phone,
            'zone': purchase.zone,
            'base': purchase.base,
            'pushcard_type': purchase.pushcard_type,
            'latitude': purchase.latitude,
            'longitude': purchase.longitude,
            'purchase_date': purchase.purchase_date.isoformat(),
            'total_sales_amount': float(purchase.total_sales_amount or 0),
            'total_quantity': purchase.total_quantity or 0,
            'sales_count': purchase.sales_count,
            'vendor_name': f"{purchase.vendor.first_name} {purchase.vendor.last_name}" if purchase.vendor else 'N/A'
        })
    
    return JsonResponse({'customers': customer_data})


def get_customer_sales_simple(request):
    vendor = request.user.id
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    # Conversion des dates
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else timezone.now().date() - timezone.timedelta(days=30)
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else timezone.now().date()
    end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
    

    purchases = Purchase.objects.filter(
        vendor=vendor,
        purchase_date__gte=start_date,
        purchase_date__lte=end_date
    ).annotate(
        total_sales_amount=Sum('purchases__total_amount'),
        total_quantity=Sum('purchases__quantity'),
        sales_count=Count('purchases')
    )
    
    customer_data = []
    
    for purchase in purchases:
        # Générer l'URL complète de la photo
        photo_url = None
        if purchase.photo:
            photo_url = request.build_absolute_uri(purchase.photo.url)
        
        customer_data.append({
            'id': purchase.id,
            'full_name': purchase.full_name,
            'phone': str(purchase.phone) if purchase.phone else None,
            'zone': str(purchase.zone) if purchase.zone else None,
            'base': str(purchase.base) if purchase.base else None,
            'pushcard_type': str(purchase.pushcard_type) if purchase.pushcard_type else None,
            'latitude': float(purchase.latitude) if purchase.latitude else None,
            'longitude': float(purchase.longitude) if purchase.longitude else None,
            'purchase_date': purchase.purchase_date.isoformat() if purchase.purchase_date else None,
            'photo_url': photo_url,
            'total_sales_amount': float(purchase.total_sales_amount or 0),
            'total_quantity': purchase.total_quantity or 0,
            'sales_count': purchase.sales_count or 0
        })
    
    return JsonResponse({'customers': customer_data})

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime
from .models import PointOfSale, Order
from django.http import JsonResponse

@api_view(['GET'])
def get_point_of_sale_orders_simple(request):
    """
    Version simplifiée sans les détails des items de commande
    Retourne les commandes des points de vente pour l'utilisateur connecté
    """
    try:
        user = request.user
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        # Conversion des dates
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else timezone.now().date() - timezone.timedelta(days=30)
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else timezone.now().date()
        
        # Récupérer les points de vente de l'utilisateur avec les statistiques de commandes
        points_of_sale = PointOfSale.objects.filter(
            user=user
        ).prefetch_related(
            'orders__items'
        ).annotate(
            total_orders_count=Count('orders', filter=Q(orders__date__gte=start_date, orders__date__lte=end_date)),
            total_revenue=Sum('orders__total', filter=Q(orders__date__gte=start_date, orders__date__lte=end_date)),
            total_items=Sum('orders__items__quantity', filter=Q(orders__date__gte=start_date, orders__date__lte=end_date))
        )
        
        pos_data = []
        
        for pos in points_of_sale:
            # Générer l'URL de l'avatar
            avatar_url = None
            if pos.avatar:
                avatar_url = request.build_absolute_uri(pos.avatar.url)
            
            pos_data.append({
                'id': pos.id,
                'name': pos.name,
                'owner': pos.owner,
                'type': pos.type,
                'type_display': pos.get_type_display(),
                'status': pos.status,
                'status_display': pos.get_status_display(),
                'phone': pos.phone,
                'email': pos.email,
                'address': pos.address,
                'district': pos.district,
                'region': pos.region,
                'commune': pos.commune,
                'latitude': float(pos.latitude) if pos.latitude else None,
                'longitude': float(pos.longitude) if pos.longitude else None,
                'avatar_url': avatar_url,
                'turnover': float(pos.turnover),
                'monthly_orders': pos.monthly_orders,
                'evaluation_score': float(pos.evaluation_score),
                'registration_date': pos.registration_date.isoformat() if pos.registration_date else None,
                'orders_summary': {
                    'total_orders': pos.total_orders_count or 0,
                    'total_revenue': float(pos.total_revenue or 0),
                    'total_items': pos.total_items or 0
                }
            })
        
        return Response({
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            'points_of_sale': pos_data
        })
        
    except ValueError as e:
        return Response(
            {'error': 'Format de date invalide. Utilisez YYYY-MM-DD'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Erreur interne: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )