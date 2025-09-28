from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404
from .models import MobileVendor, Sale
from .serializers_per import MobileVendorSerializer, VendorPerformanceSerializer
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth

class VendorViewSet(viewsets.ModelViewSet):
    queryset = MobileVendor.objects.all()
    serializer_class = MobileVendorSerializer
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """
        Endpoint pour obtenir la performance d'un vendeur
        """
        vendor = self.get_object()
        
        # Récupérer les paramètres de période
        days = request.query_params.get('days', 30)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        # Calculer la performance selon les paramètres
        if start_date and end_date:
            performance = vendor.calculate_performance(start_date, end_date)
            period_info = f"Période personnalisée: {start_date} à {end_date}"
        else:
            performance = vendor.get_recent_performance(days)
            period_info = f"Derniers {days} jours"
        
        # Statistiques détaillées
        stats = self.get_vendor_statistics(vendor, days, start_date, end_date)
        
        data = {
            'vendor_id': vendor.id,
            'vendor_name': f"{vendor.first_name} {vendor.last_name}",
            'period': period_info,
            'performance_percentage': performance,
            'statistics': stats
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def ranking(self, request):
        """
        Endpoint pour obtenir le classement de tous les vendeurs
        """
        days = request.query_params.get('days', 30)
        
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        ranking = self.get_vendors_ranking(days)
        
        return Response({
            'period_days': days,
            'total_vendors': len(ranking),
            'ranking': ranking
        })
    
    @action(detail=True, methods=['post'])
    def update_performance(self, request, pk=None):
        """
        Endpoint pour forcer la mise à jour de la performance
        """
        vendor = self.get_object()
        
        days = request.data.get('days')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if start_date and end_date:
            vendor.update_performance(start_date, end_date)
        elif days:
            vendor.update_performance()
        else:
            vendor.update_performance()
        
        return Response({
            'message': 'Performance mise à jour avec succès',
            'performance': vendor.performance
        })
    
    @action(detail=True, methods=['get'])
    def sales_history(self, request, pk=None):
        """
        Endpoint pour l'historique des ventes d'un vendeur
        """
        vendor = self.get_object()
        
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=days)
        
        sales = Sale.objects.filter(
            vendor=vendor,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).select_related('product_variant', 'customer')
        
        sales_data = []
        total_amount = 0
        
        for sale in sales:
            sales_data.append({
                'id': sale.id,
                'product_variant': str(sale.product_variant),
                'customer': str(sale.customer),
                'quantity': sale.quantity,
                'total_amount': float(sale.total_amount),
                'date': sale.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
            total_amount += float(sale.total_amount)
        
        return Response({
            'vendor': f"{vendor.first_name} {vendor.last_name}",
            'period_days': days,
            'total_sales': len(sales_data),
            'total_amount': total_amount,
            'sales': sales_data
        })
    
    def get_vendor_statistics(self, vendor, days=30, start_date=None, end_date=None):
        """
        Méthode helper pour obtenir les statistiques détaillées
        """
        if start_date and end_date:
            vendor_sales = Sale.objects.filter(
                vendor=vendor,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            total_sales = Sale.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            )
        else:
            end_date = timezone.now()
            start_date = end_date - timezone.timedelta(days=days)
            
            vendor_sales = Sale.objects.filter(
                vendor=vendor,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            total_sales = Sale.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            )
        
        vendor_total = vendor_sales.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        total_all_vendors = total_sales.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        return {
            'vendor_sales_count': vendor_sales.count(),
            'vendor_total_sales': float(vendor_total),
            'total_all_vendors_sales': float(total_all_vendors),
            'market_share_percentage': (vendor_total / total_all_vendors * 100) if total_all_vendors > 0 else 0,
            'average_daily_sales': float(vendor_total / days) if days > 0 else float(vendor_total),
            'period_start': start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date),
            'period_end': end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date),
        }
    
    def get_vendors_ranking(self, days=30):
        """
        Méthode helper pour obtenir le classement des vendeurs
        """
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=days)
        
        vendors = MobileVendor.objects.all()
        ranking = []
        
        # Obtenir le total des ventes de tous les vendeurs
        total_all_sales = Sale.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        for vendor in vendors:
            vendor_sales = Sale.objects.filter(
                vendor=vendor,
                created_at__gte=start_date,
                created_at__lte=end_date
            ).aggregate(
                total_sales=Sum('total_amount'),
                sales_count=Count('id')
            )
            
            total_sales = vendor_sales['total_sales'] or 0
            performance = (total_sales / total_all_sales * 100) if total_all_sales > 0 else 0
            
            ranking.append({
                'rank': 0,  # À calculer après
                'vendor_id': vendor.id,
                'vendor_name': f"{vendor.first_name} {vendor.last_name}",
                'point_of_sale': vendor.point_of_sale.name,
                'performance_percentage': round(performance, 2),
                'total_sales': float(total_sales),
                'sales_count': vendor_sales['sales_count'] or 0,
                'average_daily_sales': float(total_sales / days) if days > 0 else float(total_sales)
            })
        
        # Trier par performance et attribuer les rangs
        ranking.sort(key=lambda x: x['performance_percentage'], reverse=True)
        
        for i, vendor_data in enumerate(ranking):
            vendor_data['rank'] = i + 1
        
        return ranking
    
    @action(detail=False, methods=['get'])
    def sales_evolution(self, request):
        """
        Endpoint pour l'évolution des ventes par vendeur sur une période
        Retourne des données pour diagrammes en barres
        """
        # Paramètres de la requête
        period = request.query_params.get('period', 'daily')  # daily, weekly, monthly
        days = request.query_params.get('days', 30)
        vendor_ids = request.query_params.get('vendor_ids')
        
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=days)
        
        # Filtrer par vendeurs spécifiques ou tous les vendeurs
        if vendor_ids:
            vendor_ids = [int(id) for id in vendor_ids.split(',')]
            vendors = MobileVendor.objects.filter(id__in=vendor_ids)
        else:
            vendors = MobileVendor.objects.all()
        
        # Déterminer la fonction de truncation selon la période
        if period == 'weekly':
            trunc_func = TruncWeek
            period_format = 'Semaine %W'
        elif period == 'monthly':
            trunc_func = TruncMonth
            period_format = '%B %Y'
        else:  # daily par défaut
            trunc_func = TruncDate
            period_format = '%Y-%m-%d'
        
        # Données pour tous les vendeurs
        chart_data = self.get_sales_evolution_data(
            vendors, start_date, end_date, trunc_func, period_format
        )
        
        return Response(chart_data)