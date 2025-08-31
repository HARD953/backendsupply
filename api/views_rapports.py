from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count, F, Q, ExpressionWrapper, FloatField
from django.db.models.functions import TruncMonth, TruncDay, Coalesce
from datetime import datetime, timedelta
from .serializers_rapports import (
    SalesReportSerializer, InventoryReportSerializer,
    POSPerformanceSerializer, CategorySalesSerializer
)
from .models import (
    Product, ProductVariant, Order, OrderItem, 
    StockMovement, PointOfSale, Category
)
from rest_framework import status

class SalesAnalyticsView(APIView):
    def get(self, request):
        # Paramètres de période
        period = request.query_params.get('period', 'month')
        days = int(request.query_params.get('days', 30))
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Agrégation des données de vente
        orders = Order.objects.filter(
            date__range=[start_date, end_date],
            status__in=['confirmed', 'shipped', 'delivered']
        )
        
        total_sales = orders.aggregate(total=Sum('total'))['total'] or 0
        total_orders = orders.count()
        avg_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        # Meilleurs produits
        best_sellers = OrderItem.objects.filter(
            order__date__range=[start_date, end_date]
        ).values(
            'product_variant__product__name'
        ).annotate(
            total_sold=Sum('quantity'),
            revenue=Sum(F('quantity') * F('price'))
        ).order_by('-revenue')[:5]
        
        data = {
            'period': f"{days} derniers jours",
            'total_sales': total_sales,
            'total_orders': total_orders,
            'average_order_value': avg_order_value,
            'best_selling_products': list(best_sellers)
        }
        
        serializer = SalesReportSerializer(data)
        return Response(serializer.data)

class InventoryStatusView(APIView):
    def get(self, request):
        # Produits en rupture de stock
        out_of_stock = ProductVariant.objects.filter(current_stock=0).count()
        
        # Produits avec stock faible
        low_stock = ProductVariant.objects.filter(
            current_stock__gt=0,
            current_stock__lte=F('min_stock')
        ).count()
        
        # Produits surstockés
        overstocked = ProductVariant.objects.filter(
            current_stock__gt=F('max_stock')
        ).count()
        
        # Valeur totale du stock
        stock_value = ProductVariant.objects.aggregate(
            total_value=Sum(F('current_stock') * F('price'))
        )['total_value'] or 0
        
        data = {
            'total_products': Product.objects.count(),
            'low_stock_items': low_stock,
            'out_of_stock_items': out_of_stock,
            'overstocked_items': overstocked,
            'stock_value': stock_value
        }
        
        serializer = InventoryReportSerializer(data)
        return Response(serializer.data)

class POSPerformanceView(APIView):
    def get(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        pos_list = PointOfSale.objects.annotate(
            total_sales=Coalesce(Sum(
                'orders__total',
                filter=Q(
                    orders__date__range=[start_date, end_date],
                    orders__status__in=['confirmed', 'shipped', 'delivered']
                )
            ), 0),
            total_orders=Count(
                'orders',
                filter=Q(
                    orders__date__range=[start_date, end_date],
                    orders__status__in=['confirmed', 'shipped', 'delivered']
                )
            )
        ).order_by('-total_sales')
        
        serializer = POSPerformanceSerializer(pos_list, many=True)
        return Response(serializer.data)

class CategorySalesView(APIView):
    def get(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        total_sales = Order.objects.filter(
            date__range=[start_date, end_date],
            status__in=['confirmed', 'shipped', 'delivered']
        ).aggregate(total=Sum('total'))['total'] or 0
        
        categories = Category.objects.annotate(
            total_sales=Coalesce(Sum(
                'products__variants__order_items__total',
                filter=Q(
                    products__variants__order_items__order__date__range=[start_date, end_date],
                    products__variants__order_items__order__status__in=['confirmed', 'shipped', 'delivered']
                )
            ), 0)
        ).filter(total_sales__gt=0).order_by('-total_sales')
        
        # Calcul du pourcentage pour chaque catégorie
        result = []
        for category in categories:
            percentage = (category.total_sales / total_sales * 100) if total_sales > 0 else 0
            result.append({
                'id': category.id,
                'name': category.name,
                'total_sales': category.total_sales,
                'percentage': round(percentage, 2)
            })
        
        serializer = CategorySalesSerializer(result, many=True)
        return Response(serializer.data)

class SalesTrendView(APIView):
    def get(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Agrégation par jour
        daily_sales = Order.objects.filter(
            date__range=[start_date, end_date],
            status__in=['confirmed', 'shipped', 'delivered']
        ).annotate(
            day=TruncDay('date')
        ).values('day').annotate(
            total_sales=Sum('total'),
            order_count=Count('id')
        ).order_by('day')
        
        return Response(list(daily_sales))
    

