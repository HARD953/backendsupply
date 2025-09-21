# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg, F, Q, Value, DecimalField
from django.db.models.functions import Coalesce, TruncDate, TruncMonth, TruncYear
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import json

from .models import (
    PointOfSale, Product, ProductVariant, Order, OrderItem, 
    MobileVendor, VendorActivity, Purchase, Sale, Category
)
from .serializers_rep import (
    DateRangeSerializer, SalesReportSerializer, ProductPerformanceSerializer,
    VendorPerformanceSerializer, POSPerformanceSerializer, 
    CategorySalesSerializer, TimeSeriesSerializer, VendorActivitySerializer,
    PurchaseSerializer, VendorGeoSerializer
)

class ReportViewSet(viewsets.ViewSet):
    """
    ViewSet pour générer différents types de rapports incluant MobileVendor
    """
    
    def _get_date_range(self, request):
        """Helper pour extraire la plage de dates de la requête"""
        serializer = DateRangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        end_date = serializer.validated_data.get('end_date') or timezone.now().date()
        start_date = serializer.validated_data.get('start_date') or end_date - timedelta(days=30)
        
        return start_date, end_date, serializer.validated_data
    
    @action(detail=False, methods=['get'])
    def sales_summary(self, request):
        """
        Résumé des ventes avec comparaison période précédente
        Inclut les ventes des points de vente et des vendeurs ambulants
        """
        start_date, end_date, filters = self._get_date_range(request)
        point_of_sale_id = filters.get('point_of_sale_id')
        vendor_id = filters.get('vendor_id')
        
        # Filtre de base pour les commandes des points de vente
        order_filter = Q(order__date__range=[start_date, end_date])
        if point_of_sale_id:
            order_filter &= Q(order__point_of_sale_id=point_of_sale_id)
        
        # Filtre pour les ventes des vendeurs ambulants
        sale_filter = Q(created_at__date__range=[start_date, end_date])
        if vendor_id:
            sale_filter &= Q(vendor_id=vendor_id)
        if point_of_sale_id:
            sale_filter &= Q(vendor__point_of_sale_id=point_of_sale_id)
        
        # Calcul des métriques pour la période actuelle - Commandes POS
        pos_metrics = OrderItem.objects.filter(order_filter).aggregate(
            total_sales=Coalesce(Sum('total'), Value(0, output_field=DecimalField())),
            total_orders=Count('order', distinct=True),
            avg_order_value=Coalesce(Avg('order__total'), Value(0, output_field=DecimalField()))
        )
        
        # Calcul des métriques pour la période actuelle - Ventes MobileVendor
        vendor_metrics = Sale.objects.filter(sale_filter).aggregate(
            total_sales=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
            total_orders=Count('vendor_activity__related_order', distinct=True)
        )
        
        # Combinaison des métriques
        total_sales = (pos_metrics['total_sales'] or 0) + (vendor_metrics['total_sales'] or 0)
        total_orders = (pos_metrics['total_orders'] or 0) + (vendor_metrics['total_orders'] or 0)
        
        # Calcul de la valeur moyenne des commandes
        avg_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        # Calcul pour la période précédente (même durée)
        prev_start_date = start_date - (end_date - start_date) - timedelta(days=1)
        prev_end_date = start_date - timedelta(days=1)
        
        prev_order_filter = Q(order__date__range=[prev_start_date, prev_end_date])
        prev_sale_filter = Q(created_at__date__range=[prev_start_date, prev_end_date])
        
        if point_of_sale_id:
            prev_order_filter &= Q(order__point_of_sale_id=point_of_sale_id)
            prev_sale_filter &= Q(vendor__point_of_sale_id=point_of_sale_id)
        if vendor_id:
            prev_sale_filter &= Q(vendor_id=vendor_id)
            
        prev_pos_metrics = OrderItem.objects.filter(prev_order_filter).aggregate(
            total_sales=Coalesce(Sum('total'), Value(0, output_field=DecimalField()))
        )
        prev_vendor_metrics = Sale.objects.filter(prev_sale_filter).aggregate(
            total_sales=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField()))
        )
        
        prev_sales = (prev_pos_metrics['total_sales'] or 0) + (prev_vendor_metrics['total_sales'] or 0)
        
        # Calcul du pourcentage de croissance
        if prev_sales > 0:
            growth_percentage = ((total_sales - prev_sales) / prev_sales) * 100
        else:
            growth_percentage = 100 if total_sales > 0 else 0
        
        data = {
            'period': f"{start_date} to {end_date}",
            'total_sales': total_sales,
            'total_orders': total_orders,
            'average_order_value': avg_order_value,
            'growth_percentage': round(growth_percentage, 2),
            'pos_sales': pos_metrics['total_sales'] or 0,
            'vendor_sales': vendor_metrics['total_sales'] or 0
        }
        
        serializer = SalesReportSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def vendor_performance(self, request):
        """
        Performance des vendeurs ambulants avec activités et statistiques détaillées
        """
        start_date, end_date, filters = self._get_date_range(request)
        point_of_sale_id = filters.get('point_of_sale_id')
        region = filters.get('region')
        commune = filters.get('commune')
        
        # Filtre de base
        base_filter = Q(activities__timestamp__date__range=[start_date, end_date])
        if point_of_sale_id:
            base_filter &= Q(point_of_sale_id=point_of_sale_id)
        if region:
            base_filter &= Q(point_of_sale__region=region)
        if commune:
            base_filter &= Q(point_of_sale__commune=commune)
        
        vendor_performance = (
            MobileVendor.objects
            .filter(base_filter)
            .annotate(
                total_sales=Coalesce(
                    Sum('activities__sales__total_amount'), 
                    Value(0, output_field=DecimalField())
                ),
                total_orders=Count('activities__related_order', distinct=True),
                average_daily_sales=Coalesce(
                    Avg('activities__sales__total_amount'), 
                    Value(0, output_field=DecimalField())
                ),
                performance_score=Avg('performances__performance_score'),
                total_activities=Count('activities', distinct=True),
                completed_activities=Count(
                    'activities', 
                    filter=Q(activities__quantity_restante=0),
                    distinct=True
                )
            )
            .order_by('-total_sales')
        )
        
        serializer = VendorPerformanceSerializer(vendor_performance, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def vendor_activities(self, request):
        """
        Activités détaillées des vendeurs ambulants
        """
        start_date, end_date, filters = self._get_date_range(request)
        vendor_id = filters.get('vendor_id')
        point_of_sale_id = filters.get('point_of_sale_id')
        activity_type = request.query_params.get('activity_type')
        
        # Filtre de base
        base_filter = Q(timestamp__date__range=[start_date, end_date])
        if vendor_id:
            base_filter &= Q(vendor_id=vendor_id)
        if point_of_sale_id:
            base_filter &= Q(vendor__point_of_sale_id=point_of_sale_id)
        if activity_type:
            base_filter &= Q(activity_type=activity_type)
        
        activities = (
            VendorActivity.objects
            .filter(base_filter)
            .select_related('vendor', 'vendor__point_of_sale', 'related_order')
            .order_by('-timestamp')
        )
        
        serializer = VendorActivitySerializer(activities, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def vendor_geo_data(self, request):
        """
        Données géographiques des vendeurs pour la cartographie
        """
        # Récupérer les vendeurs avec leur dernière position
        today = timezone.now().date()
        
        vendors = (
            MobileVendor.objects
            .filter(activities__timestamp__date=today)
            .annotate(
                last_activity=Max('activities__timestamp'),
                total_sales_today=Coalesce(
                    Sum('activities__sales__total_amount', 
                        filter=Q(activities__timestamp__date=today)),
                    Value(0, output_field=DecimalField())
                )
            )
            .distinct()
        )
        
        # Pour chaque vendeur, trouver la dernière position connue
        vendor_data = []
        for vendor in vendors:
            last_activity = (
                VendorActivity.objects
                .filter(vendor=vendor, timestamp__date=today)
                .exclude(location__isnull=True)
                .order_by('-timestamp')
                .first()
            )
            
            if last_activity and last_activity.location:
                vendor_data.append({
                    'id': vendor.id,
                    'first_name': vendor.first_name,
                    'last_name': vendor.last_name,
                    'phone': vendor.phone,
                    'point_of_sale_name': vendor.point_of_sale.name,
                    'point_of_sale_region': vendor.point_of_sale.region,
                    'point_of_sale_commune': vendor.point_of_sale.commune,
                    'vehicle_type': vendor.vehicle_type,
                    'status': vendor.status,
                    'last_activity': last_activity.timestamp,
                    'total_sales_today': vendor.total_sales_today or 0,
                    'latitude': last_activity.location.get('latitude'),
                    'longitude': last_activity.location.get('longitude')
                })
        
        serializer = VendorGeoSerializer(vendor_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def purchase_analytics(self, request):
        """
        Analyse des achats effectués par les vendeurs ambulants
        """
        start_date, end_date, filters = self._get_date_range(request)
        vendor_id = filters.get('vendor_id')
        point_of_sale_id = filters.get('point_of_sale_id')
        zone = request.query_params.get('zone')
        
        # Filtre de base
        base_filter = Q(purchase_date__date__range=[start_date, end_date])
        if vendor_id:
            base_filter &= Q(vendor_id=vendor_id)
        if point_of_sale_id:
            base_filter &= Q(vendor__point_of_sale_id=point_of_sale_id)
        if zone:
            base_filter &= Q(zone=zone)
        
        purchases = (
            Purchase.objects
            .filter(base_filter)
            .select_related('vendor', 'vendor__point_of_sale')
            .order_by('-purchase_date')
        )
        
        # Statistiques globales
        stats = purchases.aggregate(
            total_amount=Coalesce(Sum('amount'), Value(0, output_field=DecimalField())),
            total_count=Count('id'),
            avg_amount=Coalesce(Avg('amount'), Value(0, output_field=DecimalField())),
            unique_zones=Count('zone', distinct=True),
            unique_vendors=Count('vendor', distinct=True)
        )
        
        # Achats par zone
        by_zone = (
            purchases
            .values('zone')
            .annotate(
                total_amount=Sum('amount'),
                count=Count('id'),
                avg_amount=Avg('amount')
            )
            .order_by('-total_amount')
        )
        
        # Achats par vendeur
        by_vendor = (
            purchases
            .values('vendor__first_name', 'vendor__last_name', 'vendor__point_of_sale__name')
            .annotate(
                total_amount=Sum('amount'),
                count=Count('id'),
                avg_amount=Avg('amount')
            )
            .order_by('-total_amount')
        )
        
        serializer = PurchaseSerializer(purchases, many=True)
        
        return Response({
            'summary': stats,
            'by_zone': list(by_zone),
            'by_vendor': list(by_vendor),
            'purchases': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def vendor_daily_report(self, request):
        """
        Rapport quotidien détaillé pour un vendeur spécifique
        """
        vendor_id = request.query_params.get('vendor_id')
        date = request.query_params.get('date', timezone.now().date())
        
        if not vendor_id:
            return Response({'error': 'vendor_id is required'}, status=400)
        
        try:
            vendor = MobileVendor.objects.get(id=vendor_id)
        except MobileVendor.DoesNotExist:
            return Response({'error': 'Vendor not found'}, status=404)
        
        # Activités du jour
        daily_activities = (
            VendorActivity.objects
            .filter(vendor=vendor, timestamp__date=date)
            .order_by('timestamp')
        )
        
        # Statistiques des ventes
        sales_stats = (
            Sale.objects
            .filter(vendor_activity__vendor=vendor, created_at__date=date)
            .aggregate(
                total_sales=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
                total_units=Coalesce(Sum('quantity'), Value(0)),
                avg_sale_value=Coalesce(Avg('total_amount'), Value(0, output_field=DecimalField()))
            )
        )
        
        # Produits vendus
        products_sold = (
            Sale.objects
            .filter(vendor_activity__vendor=vendor, created_at__date=date)
            .values('product_variant__product__name')
            .annotate(
                total_units=Sum('quantity'),
                total_amount=Sum('total_amount')
            )
            .order_by('-total_amount')
        )
        
        # Dernière position
        last_activity = daily_activities.last()
        last_location = last_activity.location if last_activity else None
        
        activity_serializer = VendorActivitySerializer(daily_activities, many=True)
        
        return Response({
            'vendor': {
                'id': vendor.id,
                'name': vendor.full_name,
                'point_of_sale': vendor.point_of_sale.name,
                'status': vendor.status,
                'vehicle_type': vendor.vehicle_type
            },
            'date': date,
            'activities': activity_serializer.data,
            'sales_stats': sales_stats,
            'products_sold': list(products_sold),
            'last_location': last_location
        })

class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet pour les données du dashboard incluant MobileVendor
    """
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        Aperçu général du dashboard avec les KPIs principaux incluant MobileVendor
        """
        # Récupérer les filtres
        serializer = DateRangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        start_date = serializer.validated_data.get('start_date') or timezone.now().date() - timedelta(days=30)
        end_date = serializer.validated_data.get('end_date') or timezone.now().date()
        point_of_sale_id = serializer.validated_data.get('point_of_sale_id')
        
        # Filtre de base pour les points de vente
        pos_filter = Q(orders__date__range=[start_date, end_date])
        if point_of_sale_id:
            pos_filter &= Q(id=point_of_sale_id)
        
        # Filtre de base pour les vendeurs ambulants
        vendor_filter = Q(activities__timestamp__date__range=[start_date, end_date])
        if point_of_sale_id:
            vendor_filter &= Q(point_of_sale_id=point_of_sale_id)
        
        # Calcul des KPIs pour les points de vente
        pos_kpis = PointOfSale.objects.filter(pos_filter).aggregate(
            total_sales=Coalesce(
                Sum('orders__items__total'), 
                Value(0, output_field=DecimalField())
            ),
            total_orders=Count('orders', distinct=True),
            avg_order_value=Coalesce(
                Avg('orders__total'), 
                Value(0, output_field=DecimalField())
            ),
            total_products_sold=Coalesce(Sum('orders__items__quantity'), Value(0))
        )
        
        # Calcul des KPIs pour les vendeurs ambulants
        vendor_kpis = MobileVendor.objects.filter(vendor_filter).aggregate(
            total_sales=Coalesce(
                Sum('activities__sales__total_amount'), 
                Value(0, output_field=DecimalField())
            ),
            total_activities=Count('activities', distinct=True),
            active_vendors=Count('id', distinct=True, filter=Q(status='actif'))
        )
        
        # Combinaison des KPIs
        total_sales = (pos_kpis['total_sales'] or 0) + (vendor_kpis['total_sales'] or 0)
        total_orders = pos_kpis['total_orders'] or 0
        total_activities = vendor_kpis['total_activities'] or 0
        
        # Vendeurs actifs
        active_vendors = vendor_kpis['active_vendors'] or 0
        
        # Top produits des points de vente
        pos_top_products = (
            Product.objects
            .filter(variants__order_items__order__point_of_sale__isnull=False)
            .filter(variants__order_items__order__date__range=[start_date, end_date])
            .annotate(total_sold=Sum('variants__order_items__quantity'))
            .order_by('-total_sold')[:5]
            .values('name', 'total_sold')
        )
        
        # Top produits des vendeurs ambulants
        vendor_top_products = (
            Product.objects
            .filter(variants__sales__vendor_activity__vendor__isnull=False)
            .filter(variants__sales__created_at__date__range=[start_date, end_date])
            .annotate(total_sold=Sum('variants__sales__quantity'))
            .order_by('-total_sold')[:5]
            .values('name', 'total_sold')
        )
        
        # Dernières activités des vendeurs
        recent_activities = (
            VendorActivity.objects
            .filter(timestamp__date__range=[start_date, end_date])
            .select_related('vendor', 'vendor__point_of_sale')
            .order_by('-timestamp')[:10]
            .values('id', 'vendor__first_name', 'vendor__last_name', 
                   'activity_type', 'timestamp', 'vendor__point_of_sale__name')
        )
        
        return Response({
            'kpis': {
                'total_sales': total_sales,
                'total_orders': total_orders,
                'total_activities': total_activities,
                'active_vendors': active_vendors,
                'pos_sales': pos_kpis['total_sales'] or 0,
                'vendor_sales': vendor_kpis['total_sales'] or 0
            },
            'top_products': {
                'pos': list(pos_top_products),
                'vendor': list(vendor_top_products)
            },
            'recent_activities': list(recent_activities)
        })
    
    @action(detail=False, methods=['get'])
    def vendor_map(self, request):
        """
        Données pour la carte des vendeurs en temps réel
        """
        # Vendeurs actifs aujourd'hui avec leur dernière position
        today = timezone.now().date()
        
        active_vendors = (
            MobileVendor.objects
            .filter(status='actif')
            .filter(activities__timestamp__date=today)
            .distinct()
        )
        
        vendor_data = []
        for vendor in active_vendors:
            # Dernière activité avec position
            last_activity = (
                VendorActivity.objects
                .filter(vendor=vendor, timestamp__date=today)
                .exclude(location__isnull=True)
                .order_by('-timestamp')
                .first()
            )
            
            if last_activity and last_activity.location:
                # Ventes du jour
                today_sales = (
                    Sale.objects
                    .filter(vendor_activity__vendor=vendor, created_at__date=today)
                    .aggregate(total=Coalesce(Sum('total_amount'), Value(0)))
                )['total']
                
                vendor_data.append({
                    'id': vendor.id,
                    'name': vendor.full_name,
                    'point_of_sale': vendor.point_of_sale.name,
                    'region': vendor.point_of_sale.region,
                    'commune': vendor.point_of_sale.commune,
                    'vehicle_type': vendor.vehicle_type,
                    'phone': vendor.phone,
                    'status': vendor.status,
                    'last_activity': last_activity.timestamp.isoformat() if last_activity else None,
                    'today_sales': today_sales,
                    'latitude': last_activity.location.get('latitude'),
                    'longitude': last_activity.location.get('longitude')
                })
        
        return Response(vendor_data)