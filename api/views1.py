# views.py - Version complètement corrigée sans erreurs de types
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, F, ExpressionWrapper, DecimalField, IntegerField
from django.db.models.functions import Coalesce, Cast, TruncDate, TruncMonth, TruncYear
from django.db.models import Sum, Count, Avg, Max, Min
from datetime import datetime, timedelta
from django.utils import timezone
import json

from .models import *
from .serializers1 import *

class StatisticsViewSet(viewsets.ViewSet):
    """ViewSet pour toutes les statistiques - Version complète corrigée"""
    
    # ==================== DASHBOARD & RÉSUMÉ ====================
    
    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """Résumé général du dashboard"""
        try:
            # Période actuelle (30 derniers jours)
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
            previous_start_date = start_date - timedelta(days=30)
            
            # Statistiques de base avec gestion des types
            total_sales_agg = Sale.objects.aggregate(
                total=Coalesce(
                    Sum('total_amount'), 
                    0,
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                )
            )
            total_sales = total_sales_agg['total'] or 0
            
            total_orders = Order.objects.count()
            total_mobile_vendors = MobileVendor.objects.filter(status='actif').count()
            total_points_of_sale = PointOfSale.objects.filter(status='actif').count()
            
            # Achats actifs (30 derniers jours)
            active_purchases = Purchase.objects.filter(
                purchase_date__gte=start_date
            ).count()
            
            # Calcul de la croissance avec gestion des types
            current_period_sales_agg = Sale.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).aggregate(
                total=Coalesce(
                    Sum('total_amount'), 
                    0,
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                )
            )
            current_period_sales = current_period_sales_agg['total'] or 0
            
            previous_period_sales_agg = Sale.objects.filter(
                created_at__gte=previous_start_date,
                created_at__lt=start_date
            ).aggregate(
                total=Coalesce(
                    Sum('total_amount'), 
                    0,
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                )
            )
            previous_period_sales = previous_period_sales_agg['total'] or 0
            
            sales_growth = self._calculate_growth(float(current_period_sales), float(previous_period_sales))
            
            # Croissance du revenu
            current_revenue = total_sales
            previous_revenue_agg = Sale.objects.filter(
                created_at__lt=start_date
            ).aggregate(
                total=Coalesce(
                    Sum('total_amount'), 
                    0,
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                )
            )
            previous_revenue = previous_revenue_agg['total'] or 0
            
            revenue_growth = self._calculate_growth(float(current_revenue), float(previous_revenue))
            
            data = {
                'total_sales': float(total_sales),
                'total_orders': total_orders,
                'total_mobile_vendors': total_mobile_vendors,
                'total_points_of_sale': total_points_of_sale,
                'active_purchases': active_purchases,
                'sales_growth': sales_growth,
                'revenue_growth': revenue_growth
            }
            
            return Response(data)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des statistiques: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==================== STATISTIQUES POINTS DE VENTE ====================
    
    @action(detail=False, methods=['get'])
    def points_of_sale_stats(self, request):
        """Statistiques par point de vente"""
        try:
            pos_stats = []
            
            for pos in PointOfSale.objects.all():
                # Ventes totales du POS avec gestion des types
                sales_agg = Sale.objects.filter(
                    vendor_activity__vendor__point_of_sale=pos
                ).aggregate(
                    total=Coalesce(
                        Sum('total_amount'), 
                        0,
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                )
                total_sales = sales_agg['total'] or 0
                
                # Commandes du POS
                total_orders = Order.objects.filter(point_of_sale=pos).count()
                
                # Valeur moyenne des commandes avec gestion des types
                avg_order_agg = Order.objects.filter(
                    point_of_sale=pos
                ).aggregate(
                    avg=Coalesce(
                        Avg('total'), 
                        0,
                        output_field=DecimalField(max_digits=10, decimal_places=2)
                    )
                )
                avg_order_value = avg_order_agg['avg'] or 0
                
                # Nombre de vendeurs ambulants
                mobile_vendors_count = pos.mobile_vendors.count()
                
                # Score de performance (basé sur le turnover et les ventes)
                performance_score = 0
                if pos.turnover and float(pos.turnover) > 0:
                    performance_score = min(100, (float(total_sales) / float(pos.turnover)) * 100)
                
                pos_data = {
                    'id': pos.id,
                    'name': pos.name,
                    'type': pos.type,
                    'region': pos.region,
                    'commune': pos.commune,
                    'total_sales': float(total_sales),
                    'total_orders': total_orders,
                    'average_order_value': float(avg_order_value),
                    'mobile_vendors_count': mobile_vendors_count,
                    'performance_score': round(performance_score, 2),
                    'turnover': float(pos.turnover) if pos.turnover else 0
                }
                
                pos_stats.append(pos_data)
            
            # Trier par performance décroissante
            pos_stats.sort(key=lambda x: x['performance_score'], reverse=True)
            
            return Response(pos_stats)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des stats POS: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==================== STATISTIQUES VENDEURS AMBULANTS ====================
    
    @action(detail=False, methods=['get'])
    def mobile_vendors_stats(self, request):
        """Statistiques par vendeur ambulant"""
        try:
            vendor_stats = []
            period = request.GET.get('period', '30')  # 30 jours par défaut
            
            for vendor in MobileVendor.objects.all():
                # Période de calcul
                end_date = timezone.now()
                start_date = end_date - timedelta(days=int(period))
                
                # Ventes du vendeur - agrégations séparées pour éviter les mixed types
                sales_amount_agg = Sale.objects.filter(
                    vendor=vendor,
                    created_at__gte=start_date
                ).aggregate(
                    total_sales=Coalesce(
                        Sum('total_amount'), 
                        0,
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                )
                
                sales_quantity_agg = Sale.objects.filter(
                    vendor=vendor,
                    created_at__gte=start_date
                ).aggregate(
                    total_quantity=Coalesce(
                        Sum('quantity'), 
                        0,
                        output_field=IntegerField()
                    )
                )
                
                total_sales = sales_amount_agg['total_sales'] or 0
                total_quantity = sales_quantity_agg['total_quantity'] or 0
                
                # Achats liés au vendeur - agrégations séparées
                purchases_amount_agg = Purchase.objects.filter(
                    vendor=vendor,
                    purchase_date__gte=start_date
                ).aggregate(
                    total_amount=Coalesce(
                        Sum('amount'), 
                        0,
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                )
                
                purchases_count_agg = Purchase.objects.filter(
                    vendor=vendor,
                    purchase_date__gte=start_date
                ).aggregate(
                    count=Count('id')
                )
                
                total_purchases = purchases_count_agg['count'] or 0
                total_purchase_amount = purchases_amount_agg['total_amount'] or 0
                
                # Jours d'activité
                active_days = vendor.activities.filter(
                    timestamp__gte=start_date
                ).dates('timestamp', 'day').distinct().count()
                
                # Taux d'efficacité (ventes / achats)
                efficiency_rate = 0
                if total_purchase_amount and float(total_purchase_amount) > 0:
                    efficiency_rate = (float(total_sales) / float(total_purchase_amount)) * 100
                
                # Calcul de la valeur moyenne d'achat
                average_purchase_value = 0
                if total_purchases > 0:
                    average_purchase_value = float(total_purchase_amount) / total_purchases
                
                vendor_data = {
                    'id': vendor.id,
                    'full_name': vendor.full_name,
                    'phone': vendor.phone,
                    'status': vendor.status,
                    'vehicle_type': vendor.vehicle_type,
                    'total_sales': float(total_sales),
                    'total_purchases': total_purchases,
                    'average_purchase_value': round(average_purchase_value, 2),
                    'active_days': active_days,
                    'efficiency_rate': round(efficiency_rate, 2),
                    'performance': float(vendor.performance) if vendor.performance else 0
                }
                
                vendor_stats.append(vendor_data)
            
            # Trier par performance décroissante
            vendor_stats.sort(key=lambda x: x['efficiency_rate'], reverse=True)
            
            return Response(vendor_stats)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des stats vendeurs: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==================== STATISTIQUES PRODUITS ====================
    
    @action(detail=False, methods=['get'])
    def products_stats(self, request):
        """Statistiques par produit"""
        try:
            product_stats = []
            period = request.GET.get('period', '30')
            
            for product in Product.objects.all():
                # Période de calcul
                end_date = timezone.now()
                start_date = end_date - timedelta(days=int(period))
                
                # Ventes du produit - agrégations séparées
                product_revenue_agg = Sale.objects.filter(
                    product_variant__product=product,
                    created_at__gte=start_date
                ).aggregate(
                    total_revenue=Coalesce(
                        Sum('total_amount'), 
                        0,
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                )
                
                product_quantity_agg = Sale.objects.filter(
                    product_variant__product=product,
                    created_at__gte=start_date
                ).aggregate(
                    total_quantity=Coalesce(
                        Sum('quantity'), 
                        0,
                        output_field=IntegerField()
                    )
                )
                
                total_quantity = product_quantity_agg['total_quantity'] or 0
                total_revenue = product_revenue_agg['total_revenue'] or 0
                
                # Prix moyen
                average_price = 0
                if total_quantity > 0:
                    average_price = float(total_revenue) / total_quantity
                
                # Rotation des stocks
                stock_rotation = 0
                total_stock = sum(variant.current_stock for variant in product.variants.all())
                if total_stock > 0:
                    stock_rotation = total_quantity / total_stock
                
                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'category': product.category.name if product.category else '',
                    'status': product.status,
                    'total_quantity_sold': total_quantity,
                    'total_revenue': float(total_revenue),
                    'average_price': round(average_price, 2),
                    'stock_rotation': round(stock_rotation, 2)
                }
                
                product_stats.append(product_data)
            
            # Trier par revenu décroissant
            product_stats.sort(key=lambda x: x['total_revenue'], reverse=True)
            
            return Response(product_stats)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des stats produits: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==================== STATISTIQUES ACHATS ====================
    
    @action(detail=False, methods=['get'])
    def purchases_stats(self, request):
        """Statistiques des achats"""
        try:
            purchase_stats = []
            period = request.GET.get('period', '30')
            
            # Agrégation par vendeur et zone avec gestion des types
            purchases_data = Purchase.objects.values(
                'vendor', 'zone', 'base'
            ).annotate(
                purchase_count=Count('id'),
                total_amount=Coalesce(
                    Sum('amount'), 
                    0,
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                ),
                last_purchase=Max('purchase_date')
            ).order_by('-total_amount')
            
            for data in purchases_data:
                try:
                    vendor = MobileVendor.objects.get(id=data['vendor'])
                    # Récupérer le dernier achat pour les informations détaillées
                    last_purchase = Purchase.objects.filter(
                        vendor=data['vendor'], 
                        zone=data['zone']
                    ).order_by('-purchase_date').first()
                    
                    purchase_data = {
                        'id': data['vendor'],
                        'vendor_name': vendor.full_name,
                        'first_name': last_purchase.first_name if last_purchase else '',
                        'last_name': last_purchase.last_name if last_purchase else '',
                        'zone': data['zone'],
                        'base': data['base'],
                        'purchase_count': data['purchase_count'],
                        'total_amount': float(data['total_amount']),
                        'purchase_date': data['last_purchase'].isoformat() if data['last_purchase'] else None
                    }
                    purchase_stats.append(purchase_data)
                except MobileVendor.DoesNotExist:
                    continue
            
            return Response(purchase_stats)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des stats achats: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==================== SÉRIES TEMPORELLES ====================
    
    @action(detail=False, methods=['get'])
    def sales_timeseries(self, request):
        """Série temporelle des ventes"""
        try:
            period = request.GET.get('period', 'month')  # day, week, month, year
            group_by = request.GET.get('group_by', 'day')
            
            # Définition de la période
            end_date = timezone.now()
            if period == 'week':
                start_date = end_date - timedelta(days=7)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'year':
                start_date = end_date - timedelta(days=365)
            else:  # day
                start_date = end_date - timedelta(days=1)
            
            # Agrégation par période avec gestion des types
            if group_by == 'day':
                trunc_func = TruncDate('created_at')
            elif group_by == 'month':
                trunc_func = TruncMonth('created_at')
            else:  # year
                trunc_func = TruncYear('created_at')
            
            sales_data = Sale.objects.filter(
                created_at__gte=start_date
            ).annotate(
                period=trunc_func
            ).values('period').annotate(
                value=Coalesce(
                    Sum('total_amount'), 
                    0,
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                )
            ).order_by('period')
            
            timeseries = []
            for data in sales_data:
                timeseries.append({
                    'date': data['period'].isoformat(),
                    'value': float(data['value']),
                    'label': data['period'].strftime('%Y-%m-%d')
                })
            
            return Response(timeseries)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des séries temporelles: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==================== MÉTRIQUES DE PERFORMANCE ====================
    
    @action(detail=False, methods=['get'])
    def performance_metrics(self, request):
        """Métriques de performance globales"""
        try:
            # Taux de conversion commandes -> ventes
            total_orders = Order.objects.count()
            orders_with_sales = Order.objects.filter(
                items__quantity_affecte__gt=0
            ).distinct().count()
            
            conversion_rate = (orders_with_sales / max(1, total_orders)) * 100
            
            # Taux d'utilisation des vendeurs
            active_vendors = MobileVendor.objects.filter(
                activities__timestamp__gte=timezone.now() - timedelta(days=7)
            ).distinct().count()
            total_vendors = MobileVendor.objects.count()
            vendor_utilization = (active_vendors / max(1, total_vendors)) * 100
            
            # Rotation moyenne des stocks
            total_products = Product.objects.count()
            products_with_rotation = Product.objects.filter(
                variants__current_stock__gt=0
            ).distinct().count()
            
            # Temps moyen de livraison
            delivered_orders = Order.objects.filter(status='delivered')
            avg_delivery_time = delivered_orders.aggregate(
                avg_time=Avg(F('delivery_date') - F('date'))
            )['avg_time']
            
            # Taux de réalisation des commandes
            order_fulfillment_rate = (orders_with_sales / max(1, total_orders)) * 100
            
            metrics = {
                'conversion_rate': round(conversion_rate, 2),
                'vendor_utilization_rate': round(vendor_utilization, 2),
                'stock_rotation_rate': round((products_with_rotation / max(1, total_products)) * 100, 2),
                'average_delivery_time_days': avg_delivery_time.days if avg_delivery_time else 0,
                'order_fulfillment_rate': round(order_fulfillment_rate, 2)
            }
            
            return Response(metrics)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des métriques: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==================== STATISTIQUES ZONES ====================
    
    @action(detail=False, methods=['get'])
    def zone_stats(self, request):
        """Statistiques par zone géographique"""
        try:
            zone_stats = []
            
            # Agrégation par zone
            zone_data = Purchase.objects.values('zone').annotate(
                total_sales=Coalesce(
                    Sum('amount'), 
                    0,
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                ),
                purchase_count=Count('id'),
                vendor_count=Count('vendor', distinct=True),
                avg_purchase=Coalesce(
                    Avg('amount'), 
                    0,
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            ).order_by('-total_sales')
            
            for data in zone_data:
                zone_stats.append({
                    'zone': data['zone'],
                    'total_sales': float(data['total_sales']),
                    'purchase_count': data['purchase_count'],
                    'vendor_count': data['vendor_count'],
                    'average_purchase': float(data['avg_purchase'])
                })
            
            return Response(zone_stats)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des stats zones: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==================== ANALYTIQUES REVENUS ====================
    
    @action(detail=False, methods=['get'])
    def revenue_analytics(self, request):
        """Analytiques détaillées des revenus"""
        try:
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # Filtres de base
            filters = {}
            if start_date:
                filters['created_at__gte'] = start_date
            if end_date:
                filters['created_at__lte'] = end_date
            
            # Agrégations principales
            revenue_analytics = Sale.objects.filter(**filters).aggregate(
                total_revenue=Coalesce(
                    Sum('total_amount'), 
                    0,
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                ),
                total_quantity=Coalesce(
                    Sum('quantity'), 
                    0,
                    output_field=IntegerField()
                ),
                avg_transaction=Coalesce(
                    Avg('total_amount'), 
                    0,
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                ),
                max_transaction=Coalesce(
                    Max('total_amount'), 
                    0,
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                ),
                transaction_count=Count('id')
            )
            
            # Revenu par catégorie de produit
            revenue_by_category = Sale.objects.filter(**filters).values(
                'product_variant__product__category__name'
            ).annotate(
                revenue=Coalesce(
                    Sum('total_amount'), 
                    0,
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                )
            ).annotate(
                quantity=Coalesce(
                    Sum('quantity'), 
                    0,
                    output_field=IntegerField()
                )
            ).order_by('-revenue')
            
            categories_data = []
            for item in revenue_by_category:
                categories_data.append({
                    'category': item['product_variant__product__category__name'] or 'Non catégorisé',
                    'revenue': float(item['revenue']),
                    'quantity': item['quantity']
                })
            
            # Revenu par point de vente
            revenue_by_pos = Sale.objects.filter(**filters).values(
                'vendor_activity__vendor__point_of_sale__name'
            ).annotate(
                revenue=Coalesce(
                    Sum('total_amount'), 
                    0,
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                )
            ).order_by('-revenue')
            
            pos_data = []
            for item in revenue_by_pos:
                pos_data.append({
                    'point_of_sale': item['vendor_activity__vendor__point_of_sale__name'] or 'Non assigné',
                    'revenue': float(item['revenue'])
                })
            
            analytics = {
                'summary': {
                    'total_revenue': float(revenue_analytics['total_revenue']),
                    'total_quantity': revenue_analytics['total_quantity'],
                    'average_transaction': float(revenue_analytics['avg_transaction']),
                    'max_transaction': float(revenue_analytics['max_transaction']),
                    'transaction_count': revenue_analytics['transaction_count']
                },
                'by_category': categories_data,
                'by_point_of_sale': pos_data
            }
            
            return Response(analytics)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des analytiques revenus: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==================== MÉTHODES UTILITAIRES ====================
    
    def _calculate_growth(self, current_value, previous_value):
        """Calcule le taux de croissance"""
        if previous_value == 0:
            return 100.0 if current_value > 0 else 0.0
        return round(((current_value - previous_value) / previous_value) * 100, 2)

class ReportViewSet(viewsets.ViewSet):
    """ViewSet pour la génération de rapports détaillés"""
    
    @action(detail=False, methods=['get'])
    def sales_report(self, request):
        """Rapport détaillé des ventes"""
        try:
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            pos_id = request.GET.get('pos_id')
            vendor_id = request.GET.get('vendor_id')
            
            # Filtres de base
            filters = {}
            if start_date:
                filters['created_at__gte'] = start_date
            if end_date:
                filters['created_at__lte'] = end_date
            if pos_id:
                filters['vendor_activity__vendor__point_of_sale_id'] = pos_id
            if vendor_id:
                filters['vendor_id'] = vendor_id
            
            sales_data = Sale.objects.filter(**filters).select_related(
                'product_variant__product',
                'vendor',
                'vendor_activity__vendor__point_of_sale'
            )
            
            report_data = []
            for sale in sales_data:
                report_data.append({
                    'date': sale.created_at.date().isoformat(),
                    'product_name': sale.product_variant.product.name if sale.product_variant and sale.product_variant.product else 'N/A',
                    'vendor_name': sale.vendor.full_name if sale.vendor else 'N/A',
                    'pos_name': sale.vendor_activity.vendor.point_of_sale.name if sale.vendor_activity and sale.vendor_activity.vendor and sale.vendor_activity.vendor.point_of_sale else 'N/A',
                    'quantity': sale.quantity,
                    'unit_price': float(sale.total_amount / sale.quantity) if sale.quantity > 0 else 0,
                    'total_amount': float(sale.total_amount),
                    'zone': getattr(sale.customer, 'zone', ''),
                    'latitude': sale.latitude,
                    'longitude': sale.longitude
                })
            
            return Response(report_data)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la génération du rapport: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def inventory_report(self, request):
        """Rapport d'inventaire et stock"""
        try:
            low_stock_threshold = int(request.GET.get('low_stock', 10))
            
            inventory_data = []
            for product in Product.objects.prefetch_related('variants'):
                for variant in product.variants.all():
                    stock_status = 'normal'
                    if variant.current_stock == 0:
                        stock_status = 'out_of_stock'
                    elif variant.current_stock <= variant.min_stock:
                        stock_status = 'low_stock'
                    elif variant.current_stock > variant.max_stock:
                        stock_status = 'over_stock'
                    
                    inventory_data.append({
                        'product_name': product.name,
                        'variant_name': variant.format.name if variant.format else 'Standard',
                        'current_stock': variant.current_stock,
                        'min_stock': variant.min_stock,
                        'max_stock': variant.max_stock,
                        'price': float(variant.price),
                        'stock_status': stock_status,
                        'last_updated': product.last_updated.isoformat() if product.last_updated else None
                    })
            
            return Response(inventory_data)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la génération du rapport inventaire: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )