from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, F, Q, When, Case, Value, IntegerField
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, ExtractWeek, ExtractMonth
from django.utils import timezone
from datetime import timedelta, datetime
import json
from .models import (
    Product, ProductVariant, Order, OrderItem, PointOfSale, 
    Category, Supplier, UserProfile, MobileVendor, VendorActivity, Purchase, Sale
)
from .serializers_rep import (
    ReportFilterSerializer, SalesReportSerializer, StockReportSerializer,
    ClientReportSerializer, OrderReportSerializer, SupplierReportSerializer,
    GeneratedReportSerializer
)

class ReportView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupère les rapports en fonction des filtres"""
        filter_serializer = ReportFilterSerializer(data=request.query_params)
        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        filters = filter_serializer.validated_data
        report_type = filters.get('report_type', 'ventes')
        start_date = filters.get('start_date', timezone.now() - timedelta(days=30))
        end_date = filters.get('end_date', timezone.now())
        point_of_sale = filters.get('point_of_sale')
        category = filters.get('category')
        
        # Déterminer quel rapport générer
        if report_type == 'ventes':
            report_data = self.get_sales_report(start_date, end_date, point_of_sale, category)
            serializer = SalesReportSerializer(report_data)
        elif report_type == 'stocks':
            report_data = self.get_stock_report(point_of_sale, category)
            serializer = StockReportSerializer(report_data)
        elif report_type == 'clients':
            report_data = self.get_client_report(start_date, end_date, point_of_sale)
            serializer = ClientReportSerializer(report_data)
        elif report_type == 'commandes':
            report_data = self.get_order_report(start_date, end_date, point_of_sale, category)
            serializer = OrderReportSerializer(report_data)
        elif report_type == 'fournisseurs':
            report_data = self.get_supplier_report(start_date, end_date, point_of_sale, category)
            serializer = SupplierReportSerializer(report_data)
        else:
            return Response({"error": "Type de rapport non valide"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.data)
    
    def get_sales_report(self, start_date, end_date, point_of_sale, category):
        """Génère le rapport des ventes"""
        # Filtrer les ventes par période et point de vente
        sales_filter = Q(created_at__date__gte=start_date, created_at__date__lte=end_date)
        if point_of_sale:
            sales_filter &= Q(vendor_activity__vendor__point_of_sale=point_of_sale)
        
        # Agrégation des données de vente
        sales_data = Sale.objects.filter(sales_filter).aggregate(
            total_sales=Sum('total_amount'),
            total_quantity=Sum('quantity')
        )
        
        # Calcul de l'évolution par rapport à la période précédente
        prev_start_date = start_date - timedelta(days=(end_date - start_date).days)
        prev_sales_data = Sale.objects.filter(
            created_at__date__gte=prev_start_date, 
            created_at__date__lte=start_date - timedelta(days=1)
        ).aggregate(total_sales=Sum('total_amount'))
        
        prev_total = prev_sales_data['total_sales'] or 0
        current_total = sales_data['total_sales'] or 0
        
        if prev_total > 0:
            evolution_percent = ((current_total - prev_total) / prev_total) * 100
            evolution = f"{'+' if evolution_percent >= 0 else ''}{evolution_percent:.1f}%"
        else:
            evolution = "+100%" if current_total > 0 else "0%"
        
        # Données pour le graphique par période
        chart_data = []
        if (end_date - start_date).days <= 7:
            # Données journalières
            daily_sales = Sale.objects.filter(sales_filter).annotate(
                day=TruncDay('created_at')
            ).values('day').annotate(
                total=Sum('total_amount')
            ).order_by('day')
            
            for day in daily_sales:
                chart_data.append({
                    'name': day['day'].strftime('%a'),
                    'ventes': float(day['total'] or 0)
                })
        else:
            # Données hebdomadaires
            weekly_sales = Sale.objects.filter(sales_filter).annotate(
                week=ExtractWeek('created_at')
            ).values('week').annotate(
                total=Sum('total_amount')
            ).order_by('week')
            
            for week in weekly_sales:
                chart_data.append({
                    'name': f"Sem {week['week']}",
                    'ventes': float(week['total'] or 0)
                })
        
        # Ventes par produit
        by_product = Sale.objects.filter(sales_filter).values(
            'product_variant__product__name'
        ).annotate(
            total=Sum('total_amount'),
            quantity=Sum('quantity')
        ).order_by('-total')[:10]
        
        product_data = []
        for product in by_product:
            product_data.append({
                'name': product['product_variant__product__name'],
                'value': float(product['total'] or 0),
                'quantity': product['quantity'] or 0
            })
        
        # Ventes par catégorie
        by_category = Sale.objects.filter(sales_filter).values(
            'product_variant__product__category__name'
        ).annotate(
            total=Sum('total_amount')
        ).order_by('-total')
        
        category_data = []
        total_sales = sales_data['total_sales'] or 1  # Éviter la division par zéro
        
        for category in by_category:
            percent = (category['total'] or 0) / total_sales * 100
            category_data.append({
                'name': category['product_variant__product__category__name'] or 'Non catégorisé',
                'value': round(percent, 1)
            })
        
        # Données tabulaires détaillées
        table_data = []
        detailed_sales = Sale.objects.filter(sales_filter).select_related(
            'product_variant__product'
        )[:50]
        
        for sale in detailed_sales:
            table_data.append({
                'id': sale.id,
                'produit': sale.product_variant.product.name,
                'category': sale.product_variant.product.category.name if sale.product_variant.product.category else 'Non catégorisé',
                'quantite': sale.quantity,
                'montant': float(sale.total_amount)
            })
        
        return {
            'total': float(current_total),
            'evolution': evolution,
            'point_of_sale': point_of_sale.name if point_of_sale else 'Tous',
            'chart_data': chart_data,
            'by_product': product_data,
            'by_category': category_data,
            'table_data': table_data
        }
    
    def get_stock_report(self, point_of_sale, category):
        """Génère le rapport des stocks"""
        # Filtrer les produits par point de vente et catégorie
        stock_filter = Q()
        if point_of_sale:
            stock_filter &= Q(point_of_sale=point_of_sale)
        if category:
            stock_filter &= Q(category=category)
        
        # Statistiques générales
        products = Product.objects.filter(stock_filter)
        variants = ProductVariant.objects.filter(product__in=products)
        
        total_products = products.count()
        low_stock = variants.filter(current_stock__lte=F('min_stock')).count()
        
        # Données pour le graphique des niveaux de stock
        chart_data = []
        for variant in variants[:10]:  # Limiter aux 10 premiers pour le graphique
            chart_data.append({
                'name': variant.product.name,
                'stock': variant.current_stock,
                'seuil': variant.min_stock,
                'category': variant.product.category.name if variant.product.category else 'Non catégorisé'
            })
        
        # Répartition par catégorie
        by_category = products.values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        category_data = []
        for cat in by_category:
            percent = (cat['count'] or 0) / total_products * 100 if total_products > 0 else 0
            category_data.append({
                'name': cat['category__name'] or 'Non catégorisé',
                'value': round(percent, 1)
            })
        
        # Distribution des statuts
        status_distribution = [
            {
                'name': 'En stock',
                'value': variants.filter(current_stock__gt=F('min_stock')).count()
            },
            {
                'name': 'Stock faible',
                'value': variants.filter(
                    current_stock__lte=F('min_stock'), 
                    current_stock__gt=0
                ).count()
            },
            {
                'name': 'Rupture',
                'value': variants.filter(current_stock=0).count()
            }
        ]
        
        return {
            'total_products': total_products,
            'low_stock': low_stock,
            'point_of_sale': point_of_sale.name if point_of_sale else 'Tous',
            'chart_data': chart_data,
            'by_category': category_data,
            'status_distribution': status_distribution
        }
    
    def get_client_report(self, start_date, end_date, point_of_sale):
        """Génère le rapport clients"""
        # Filtrer les clients par période et point de vente
        client_filter = Q(created_at__date__gte=start_date, created_at__date__lte=end_date)
        if point_of_sale:
            client_filter &= Q(point_of_sale=point_of_sale)
        
        # Compter les nouveaux clients vs clients fidèles
        # Cette logique dépend de votre modèle de données
        # Ici, on suppose que les clients sont enregistrés dans le modèle Purchase
        
        purchases = Purchase.objects.filter(client_filter)
        clients = purchases.values('first_name', 'last_name', 'phone').distinct()
        
        # Pour simplifier, on considère tous les clients comme nouveaux
        # Dans une implémentation réelle, il faudrait vérifier les achats précédents
        new_clients = clients.count()
        returning_clients = 0  # À implémenter selon la logique métier
        
        # Données pour le graphique d'évolution
        chart_data = []
        if (end_date - start_date).days <= 30:
            # Données journalières
            daily_clients = purchases.annotate(
                day=TruncDay('created_at')
            ).values('day').annotate(
                count=Count('id', distinct=True)
            ).order_by('day')
            
            for day in daily_clients:
                chart_data.append({
                    'name': day['day'].strftime('%d/%m'),
                    'nouveaux': day['count'],
                    'retours': 0  # À implémenter
                })
        else:
            # Données mensuelles
            monthly_clients = purchases.annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                count=Count('id', distinct=True)
            ).order_by('month')
            
            for month in monthly_clients:
                chart_data.append({
                    'name': month['month'].strftime('%b'),
                    'nouveaux': month['count'],
                    'retours': 0  # À implémenter
                })
        
        # Répartition par région (à adapter selon votre modèle)
        by_region = purchases.values('zone').annotate(
            count=Count('id', distinct=True)
        ).order_by('-count')[:5]
        
        region_data = [{'name': r['zone'], 'value': r['count']} for r in by_region]
        
        # Répartition par commune (à adapter selon votre modèle)
        by_commune = purchases.values('zone').annotate(
            count=Count('id', distinct=True)
        ).order_by('-count')[:5]
        
        commune_data = [{'name': c['zone'], 'value': c['count']} for c in by_commune]
        
        return {
            'new_clients': new_clients,
            'returning_clients': returning_clients,
            'point_of_sale': point_of_sale.name if point_of_sale else 'Tous',
            'chart_data': chart_data,
            'by_region': region_data,
            'by_commune': commune_data
        }
    
    def get_order_report(self, start_date, end_date, point_of_sale, category):
        """Génère le rapport des commandes"""
        # Filtrer les commandes par période et point de vente
        order_filter = Q(date__gte=start_date, date__lte=end_date)
        if point_of_sale:
            order_filter &= Q(point_of_sale=point_of_sale)
        
        orders = Order.objects.filter(order_filter)
        
        # Statistiques générales
        total_orders = orders.count()
        completed = orders.filter(status='delivered').count()
        pending = orders.filter(status__in=['pending', 'confirmed', 'shipped']).count()
        cancelled = orders.filter(status='cancelled').count()
        
        # Revenu total et valeur moyenne
        revenue_data = orders.aggregate(
            total_revenue=Sum('total'),
            avg_order_value=Avg('total')
        )
        
        total_revenue = revenue_data['total_revenue'] or 0
        avg_order_value = revenue_data['avg_order_value'] or 0
        
        # Données pour le graphique par période
        chart_data = []
        if (end_date - start_date).days <= 7:
            # Données journalières
            daily_orders = orders.annotate(
                day=TruncDay('date')
            ).values('day').annotate(
                commandes=Count('id'),
                revenu=Sum('total')
            ).order_by('day')
            
            for day in daily_orders:
                chart_data.append({
                    'name': day['day'].strftime('%a'),
                    'commandes': day['commandes'],
                    'revenu': float(day['revenu'] or 0)
                })
        else:
            # Données hebdomadaires
            weekly_orders = orders.annotate(
                week=ExtractWeek('date')
            ).values('week').annotate(
                commandes=Count('id'),
                revenu=Sum('total')
            ).order_by('week')
            
            for week in weekly_orders:
                chart_data.append({
                    'name': f"Sem {week['week']}",
                    'commandes': week['commandes'],
                    'revenu': float(week['revenu'] or 0)
                })
        
        # Répartition par statut
        by_status = [
            {'name': 'Livrées', 'value': completed},
            {'name': 'En attente', 'value': pending},
            {'name': 'Annulées', 'value': cancelled}
        ]
        
        # Revenu par catégorie
        by_category = OrderItem.objects.filter(order__in=orders).values(
            'product_variant__product__category__name'
        ).annotate(
            count=Count('id'),
            revenu=Sum(F('quantity') * F('price'))
        ).order_by('-revenu')
        
        category_data = []
        for cat in by_category:
            category_data.append({
                'name': cat['product_variant__product__category__name'] or 'Non catégorisé',
                'value': (cat['count'] or 0) / total_orders * 100 if total_orders > 0 else 0,
                'revenu': float(cat['revenu'] or 0)
            })
        
        return {
            'total_orders': total_orders,
            'completed': completed,
            'pending': pending,
            'cancelled': cancelled,
            'point_of_sale': point_of_sale.name if point_of_sale else 'Tous',
            'total_revenue': float(total_revenue),
            'average_order_value': float(avg_order_value),
            'chart_data': chart_data,
            'by_status': by_status,
            'by_category': category_data
        }
    
    def get_supplier_report(self, start_date, end_date, point_of_sale, category):
        """Génère le rapport fournisseurs"""
        # Filtrer les produits par point de vente et catégorie
        product_filter = Q()
        if point_of_sale:
            product_filter &= Q(point_of_sale=point_of_sale)
        if category:
            product_filter &= Q(category=category)
        
        products = Product.objects.filter(product_filter)
        suppliers = Supplier.objects.filter(products__in=products).distinct()
        
        # Statistiques générales
        total_suppliers = suppliers.count()
        active_suppliers = suppliers.filter(products__isnull=False).distinct().count()
        total_products = products.count()
        
        # Données pour le graphique d'activité
        chart_data = []
        if (end_date - start_date).days <= 180:  # 6 mois
            # Données mensuelles
            for i in range(6):
                month_date = end_date - timedelta(days=30*i)
                month_start = month_date.replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                month_products = products.filter(created_at__date__range=[month_start, month_end])
                month_orders = Order.objects.filter(
                    items__product_variant__product__in=month_products,
                    date__range=[month_start, month_end]
                ).distinct()
                
                chart_data.insert(0, {
                    'name': month_start.strftime('%b'),
                    'commandes': month_orders.count(),
                    'produits': month_products.count()
                })
        
        # Répartition par fournisseur
        by_supplier = products.values('supplier__name').annotate(
            count=Count('id'),
            product_count=Count('id', distinct=True)
        ).order_by('-count')[:5]
        
        supplier_data = []
        for supplier in by_supplier:
            supplier_data.append({
                'name': supplier['supplier__name'],
                'value': (supplier['count'] or 0) / total_products * 100 if total_products > 0 else 0,
                'produits': supplier['product_count']
            })
        
        # Répartition par catégorie
        by_category = products.values('category__name').annotate(
            count=Count('id'),
            supplier_count=Count('supplier', distinct=True)
        ).order_by('-count')
        
        category_data = []
        for cat in by_category:
            category_data.append({
                'name': cat['category__name'] or 'Non catégorisé',
                'value': (cat['count'] or 0) / total_products * 100 if total_products > 0 else 0,
                'fournisseurs': cat['supplier_count']
            })
        
        return {
            'total_suppliers': total_suppliers,
            'active_suppliers': active_suppliers,
            'total_products': total_products,
            'point_of_sale': point_of_sale.name if point_of_sale else 'Tous',
            'chart_data': chart_data,
            'by_supplier': supplier_data,
            'by_category': category_data
        }

class ReportListCreateView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupère la liste des rapports générés"""
        # Dans une implémentation réelle, vous auriez un modèle Report
        # Pour l'instant, on retourne une liste vide ou des données mockées
        reports = []  # À remplacer par Report.objects.filter(user=request.user)
        
        # Données mockées pour l'exemple
        mock_reports = [
            {
                'id': 1,
                'title': 'Rapport des ventes mensuelles',
                'type': 'ventes',
                'period': 'Mai 2023',
                'generated_at': '2023-05-31T14:30:00Z',
                'download_url': '#',
                'size': '1.2 MB',
                'data': {}
            }
        ]
        
        serializer = GeneratedReportSerializer(mock_reports, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Génère un nouveau rapport"""
        filter_serializer = ReportFilterSerializer(data=request.data)
        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        filters = filter_serializer.validated_data
        report_type = filters.get('report_type', 'ventes')
        
        # Générer le rapport
        report_view = ReportView()
        report_view.request = request
        
        if report_type == 'ventes':
            report_data = report_view.get_sales_report(
                filters.get('start_date', timezone.now() - timedelta(days=30)),
                filters.get('end_date', timezone.now()),
                filters.get('point_of_sale'),
                filters.get('category')
            )
        elif report_type == 'stocks':
            report_data = report_view.get_stock_report(
                filters.get('point_of_sale'),
                filters.get('category')
            )
        elif report_type == 'clients':
            report_data = report_view.get_client_report(
                filters.get('start_date', timezone.now() - timedelta(days=30)),
                filters.get('end_date', timezone.now()),
                filters.get('point_of_sale')
            )
        elif report_type == 'commandes':
            report_data = report_view.get_order_report(
                filters.get('start_date', timezone.now() - timedelta(days=30)),
                filters.get('end_date', timezone.now()),
                filters.get('point_of_sale'),
                filters.get('category')
            )
        elif report_type == 'fournisseurs':
            report_data = report_view.get_supplier_report(
                filters.get('start_date', timezone.now() - timedelta(days=30)),
                filters.get('end_date', timezone.now()),
                filters.get('point_of_sale'),
                filters.get('category')
            )
        else:
            return Response({"error": "Type de rapport non valide"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Dans une implémentation réelle, vous sauvegarderiez le rapport en base
        # Pour l'instant, on retourne juste les données
        
        # Créer un objet rapport simulé
        report = {
            'id': int(timezone.now().timestamp()),
            'title': f"Rapport {report_type} - {timezone.now().strftime('%d/%m/%Y')}",
            'type': report_type,
            'period': f"{filters.get('start_date', timezone.now() - timedelta(days=30)).strftime('%b %Y')} - {filters.get('end_date', timezone.now()).strftime('%b %Y')}",
            'generated_at': timezone.now(),
            'download_url': '#',
            'size': '1.0 MB',  # Taille simulée
            'data': report_data
        }
        
        serializer = GeneratedReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class DashboardDataView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupère les données pour le tableau de bord"""
        # Données pour les graphiques du tableau de bord
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Rapports par type
        reports_by_type = [
            {'name': 'Ventes', 'value': 5, 'icon': 'ShoppingBag'},
            {'name': 'Stocks', 'value': 3, 'icon': 'Package'},
            {'name': 'Clients', 'value': 2, 'icon': 'Users'},
            {'name': 'Commandes', 'value': 4, 'icon': 'ShoppingCart'},
            {'name': 'Fournisseurs', 'value': 1, 'icon': 'Truck'}
        ]
        
        # Activité récente (mock data)
        recent_activity = [
            {'month': 'Mai', 'générés': 3, 'téléchargés': 8},
            {'month': 'Juin', 'générés': 5, 'téléchargés': 12},
            {'month': 'Juil', 'générés': 2, 'téléchargés': 6},
            {'month': 'Août', 'générés': 4, 'téléchargés': 9}
        ]
        
        # Derniers rapports générés (mock data)
        recent_reports = [
            {
                'id': 1,
                'title': 'Rapport des ventes mensuelles',
                'type': 'ventes',
                'point_of_sale': 'Supermarché Abidjan',
                'period': 'Mai 2023',
                'date': '2023-05-31',
                'size': '1.2 MB'
            },
            {
                'id': 2,
                'title': 'État des stocks',
                'type': 'stocks',
                'point_of_sale': 'Boutique Yopougon',
                'period': 'Juin 2023',
                'date': '2023-06-15',
                'size': '0.8 MB'
            }
        ]
        
        return Response({
            'reports_by_type': reports_by_type,
            'recent_activity': recent_activity,
            'recent_reports': recent_reports
        })  