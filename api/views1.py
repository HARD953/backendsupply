# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce
from datetime import datetime, timedelta
import json
from .models import *

from .serializers1 import *

class StatisticsViewSet(viewsets.ViewSet):
    """ViewSet pour toutes les statistiques"""
    
    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """Résumé général du dashboard"""
        try:
            # Période actuelle (30 derniers jours)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            previous_start_date = start_date - timedelta(days=30)
            
            # Statistiques de base
            total_sales = Sale.objects.aggregate(
                total=Coalesce(Sum('total_amount'), 0)
            )['total']
            
            total_orders = Order.objects.count()
            total_mobile_vendors = MobileVendor.objects.filter(status='actif').count()
            total_points_of_sale = PointOfSale.objects.filter(status='actif').count()
            
            # Achats actifs (30 derniers jours)
            active_purchases = Purchase.objects.filter(
                purchase_date__gte=start_date
            ).count()
            
            # Calcul de la croissance
            current_period_sales = Sale.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).aggregate(total=Coalesce(Sum('total_amount'), 0))['total']
            
            previous_period_sales = Sale.objects.filter(
                created_at__gte=previous_start_date,
                created_at__lt=start_date
            ).aggregate(total=Coalesce(Sum('total_amount'), 0))['total']
            
            sales_growth = self._calculate_growth(current_period_sales, previous_period_sales)
            
            # Croissance du revenu
            current_revenue = total_sales
            previous_revenue = Sale.objects.filter(
                created_at__lt=start_date
            ).aggregate(total=Coalesce(Sum('total_amount'), 0))['total']
            
            revenue_growth = self._calculate_growth(current_revenue, previous_revenue)
            
            data = {
                'total_sales': total_sales,
                'total_orders': total_orders,
                'total_mobile_vendors': total_mobile_vendors,
                'total_points_of_sale': total_points_of_sale,
                'active_purchases': active_purchases,
                'sales_growth': sales_growth,
                'revenue_growth': revenue_growth
            }
            
            serializer = DashboardSummarySerializer(data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des statistiques: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def points_of_sale_stats(self, request):
        """Statistiques par point de vente"""
        try:
            pos_stats = []
            
            for pos in PointOfSale.objects.all():
                # Ventes totales du POS
                total_sales = Sale.objects.filter(
                    vendor_activity__vendor__point_of_sale=pos
                ).aggregate(total=Coalesce(Sum('total_amount'), 0))['total']
                
                # Commandes du POS
                total_orders = Order.objects.filter(point_of_sale=pos).count()
                
                # Valeur moyenne des commandes
                avg_order_value = Order.objects.filter(
                    point_of_sale=pos
                ).aggregate(avg=Coalesce(Avg('total'), 0))['avg']
                
                # Nombre de vendeurs ambulants
                mobile_vendors_count = pos.mobile_vendors.count()
                
                # Score de performance (basé sur le turnover et les ventes)
                performance_score = min(100, (total_sales / max(1, pos.turnover)) * 100)
                
                pos_data = {
                    'id': pos.id,
                    'name': pos.name,
                    'type': pos.type,
                    'region': pos.region,
                    'commune': pos.commune,
                    'total_sales': total_sales,
                    'total_orders': total_orders,
                    'average_order_value': avg_order_value,
                    'mobile_vendors_count': mobile_vendors_count,
                    'performance_score': round(performance_score, 2),
                    'turnover': pos.turnover
                }
                
                pos_stats.append(pos_data)
            
            # Trier par performance décroissante
            pos_stats.sort(key=lambda x: x['performance_score'], reverse=True)
            
            serializer = POSStatisticSerializer(pos_stats, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des stats POS: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def mobile_vendors_stats(self, request):
        """Statistiques par vendeur ambulant"""
        try:
            vendor_stats = []
            period = request.GET.get('period', '30')  # 30 jours par défaut
            
            for vendor in MobileVendor.objects.all():
                # Période de calcul
                end_date = datetime.now()
                start_date = end_date - timedelta(days=int(period))
                
                # Ventes du vendeur
                vendor_sales = Sale.objects.filter(
                    vendor=vendor,
                    created_at__gte=start_date
                ).aggregate(
                    total_sales=Coalesce(Sum('total_amount'), 0),
                    total_quantity=Coalesce(Sum('quantity'), 0)
                )
                
                # Achats liés au vendeur
                purchases = Purchase.objects.filter(
                    vendor=vendor,
                    purchase_date__gte=start_date
                )
                total_purchases = purchases.count()
                total_purchase_amount = purchases.aggregate(
                    total=Coalesce(Sum('amount'), 0)
                )['total']
                
                # Jours d'activité
                active_days = vendor.activities.filter(
                    timestamp__gte=start_date
                ).dates('timestamp', 'day').distinct().count()
                
                # Taux d'efficacité (ventes / achats)
                efficiency_rate = 0
                if total_purchase_amount > 0:
                    efficiency_rate = (vendor_sales['total_sales'] / total_purchase_amount) * 100
                
                vendor_data = {
                    'id': vendor.id,
                    'full_name': vendor.full_name,
                    'phone': vendor.phone,
                    'status': vendor.status,
                    'vehicle_type': vendor.vehicle_type,
                    'total_sales': vendor_sales['total_sales'],
                    'total_purchases': total_purchases,
                    'average_purchase_value': total_purchase_amount / max(1, total_purchases),
                    'active_days': active_days,
                    'efficiency_rate': round(efficiency_rate, 2),
                    'performance': vendor.performance
                }
                
                vendor_stats.append(vendor_data)
            
            # Trier par performance décroissante
            vendor_stats.sort(key=lambda x: x['efficiency_rate'], reverse=True)
            
            serializer = MobileVendorStatisticSerializer(vendor_stats, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des stats vendeurs: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def products_stats(self, request):
        """Statistiques par produit"""
        try:
            product_stats = []
            period = request.GET.get('period', '30')
            
            for product in Product.objects.all():
                # Période de calcul
                end_date = datetime.now()
                start_date = end_date - timedelta(days=int(period))
                
                # Ventes du produit
                product_sales = Sale.objects.filter(
                    product_variant__product=product,
                    created_at__gte=start_date
                ).aggregate(
                    total_quantity=Coalesce(Sum('quantity'), 0),
                    total_revenue=Coalesce(Sum('total_amount'), 0)
                )
                
                # Prix moyen
                average_price = 0
                if product_sales['total_quantity'] > 0:
                    average_price = product_sales['total_revenue'] / product_sales['total_quantity']
                
                # Rotation des stocks
                stock_rotation = 0
                total_stock = sum(variant.current_stock for variant in product.variants.all())
                if total_stock > 0:
                    stock_rotation = product_sales['total_quantity'] / total_stock
                
                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'category': product.category.name if product.category else '',
                    'status': product.status,
                    'total_quantity_sold': product_sales['total_quantity'],
                    'total_revenue': product_sales['total_revenue'],
                    'average_price': round(average_price, 2),
                    'stock_rotation': round(stock_rotation, 2)
                }
                
                product_stats.append(product_data)
            
            # Trier par revenu décroissant
            product_stats.sort(key=lambda x: x['total_revenue'], reverse=True)
            
            serializer = ProductStatisticSerializer(product_stats, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des stats produits: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def purchases_stats(self, request):
        """Statistiques des achats"""
        try:
            purchase_stats = []
            period = request.GET.get('period', '30')
            
            # Agrégation par vendeur et zone
            purchases_data = Purchase.objects.values(
                'vendor', 'zone', 'base'
            ).annotate(
                purchase_count=Count('id'),
                total_amount=Sum('amount'),
                last_purchase=Max('purchase_date')
            ).order_by('-total_amount')
            
            for data in purchases_data:
                try:
                    vendor = MobileVendor.objects.get(id=data['vendor'])
                    purchase_data = {
                        'id': data['vendor'],
                        'vendor_name': vendor.full_name,
                        'first_name': '',  # Remplir avec les données d'achat récent
                        'last_name': '',
                        'zone': data['zone'],
                        'base': data['base'],
                        'purchase_count': data['purchase_count'],
                        'total_amount': data['total_amount'],
                        'purchase_date': data['last_purchase']
                    }
                    purchase_stats.append(purchase_data)
                except MobileVendor.DoesNotExist:
                    continue
            
            serializer = PurchaseStatisticSerializer(purchase_stats, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des stats achats: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def sales_timeseries(self, request):
        """Série temporelle des ventes"""
        try:
            period = request.GET.get('period', 'month')  # day, week, month, year
            group_by = request.GET.get('group_by', 'day')
            
            # Définition de la période
            end_date = datetime.now()
            if period == 'week':
                start_date = end_date - timedelta(days=7)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'year':
                start_date = end_date - timedelta(days=365)
            else:  # day
                start_date = end_date - timedelta(days=1)
            
            # Agrégation par période
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
                value=Sum('total_amount')
            ).order_by('period')
            
            timeseries = []
            for data in sales_data:
                timeseries.append({
                    'date': data['period'],
                    'value': data['value'],
                    'label': data['period'].strftime('%Y-%m-%d')
                })
            
            serializer = TimeSeriesSerializer(timeseries, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des séries temporelles: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def performance_metrics(self, request):
        """Métriques de performance globales"""
        try:
            # Taux de conversion commandes -> ventes
            total_orders = Order.objects.count()
            orders_with_sales = Order.objects.filter(
                items__orderitem__quantity_affecte__gt=0
            ).distinct().count()
            
            conversion_rate = (orders_with_sales / max(1, total_orders)) * 100
            
            # Taux d'utilisation des vendeurs
            active_vendors = MobileVendor.objects.filter(
                activities__timestamp__gte=datetime.now() - timedelta(days=7)
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
            
            metrics = {
                'conversion_rate': round(conversion_rate, 2),
                'vendor_utilization_rate': round(vendor_utilization, 2),
                'stock_rotation_rate': round((products_with_rotation / max(1, total_products)) * 100, 2),
                'average_delivery_time_days': avg_delivery_time.days if avg_delivery_time else 0,
                'order_fulfillment_rate': round((orders_with_sales / max(1, total_orders)) * 100, 2)
            }
            
            return Response(metrics)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des métriques: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
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
                    'date': sale.created_at.date(),
                    'product_name': sale.product_variant.product.name,
                    'vendor_name': sale.vendor.full_name,
                    'pos_name': sale.vendor_activity.vendor.point_of_sale.name,
                    'quantity': sale.quantity,
                    'unit_price': sale.total_amount / sale.quantity,
                    'total_amount': sale.total_amount,
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
            low_stock_threshold = request.GET.get('low_stock', 10)
            
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
                        'price': variant.price,
                        'stock_status': stock_status,
                        'last_updated': product.last_updated
                    })
            
            return Response(inventory_data)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la génération du rapport inventaire: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )