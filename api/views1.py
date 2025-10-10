# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import HttpResponse
import json
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

from .models import *
from .serializers1 import *

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Report.objects.all()
        
        # Filtrage par type de rapport
        report_type = self.request.query_params.get('type', None)
        if report_type:
            queryset = queryset.filter(report_type=report_type)
            
        # Filtrage par point de vente
        point_of_sale = self.request.query_params.get('point_of_sale', None)
        if point_of_sale:
            queryset = queryset.filter(point_of_sale_id=point_of_sale)
            
        # Filtrage par date
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date and end_date:
            queryset = queryset.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
            
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        serializer = ReportGenerationSerializer(data=request.data)
        if serializer.is_valid():
            return self._generate_report(serializer.validated_data, request.user)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _generate_report(self, data, user):
        report_type = data['report_type']
        start_date = data['start_date']
        end_date = data['end_date']
        point_of_sale = data.get('point_of_sale')
        category = data.get('category')
        format_type = data.get('format', 'pdf')

        # Créer l'entrée du rapport
        report = Report.objects.create(
            title=f"Rapport {report_type}",
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            point_of_sale=point_of_sale,
            generated_by=user,
            filters={
                'category_id': category.id if category else None,
                'point_of_sale_id': point_of_sale.id if point_of_sale else None
            }
        )

        try:
            # Générer les données du rapport selon le type
            report_data = self._generate_report_data(report_type, start_date, end_date, point_of_sale, category)
            report.data = report_data
            report.is_generated = True
            
            # Générer le fichier si nécessaire
            if format_type != 'json':
                file_content = self._generate_file(report_data, report_type, format_type)
                filename = f"report_{report.id}_{report_type}.{format_type}"
                report.file.save(filename, file_content)
                report.size = report.get_file_size()
            
            report.save()
            
            serializer = self.get_serializer(report)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            report.delete()
            return Response(
                {'error': f'Erreur lors de la génération du rapport: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generate_report_data(self, report_type, start_date, end_date, point_of_sale, category):
        # Filtrer par période
        date_filter = Q(created_at__date__gte=start_date, created_at__date__lte=end_date)
        
        if report_type == 'points_vente':
            return self._generate_points_of_sale_report(date_filter, point_of_sale)
        elif report_type == 'ventes':
            return self._generate_sales_report(date_filter, point_of_sale, category)
        elif report_type == 'stocks':
            return self._generate_stocks_report(point_of_sale, category)
        elif report_type == 'commandes':
            return self._generate_orders_report(date_filter, point_of_sale)
        elif report_type == 'vendeurs':
            return self._generate_vendors_report(date_filter, point_of_sale)
        elif report_type == 'clients':
            return self._generate_purchases_report(date_filter, point_of_sale)
        elif report_type == 'performance':
            return self._generate_performance_report(date_filter, point_of_sale)
        else:
            return {}

    def _generate_points_of_sale_report(self, date_filter, point_of_sale):
        queryset = PointOfSale.objects.all()
        if point_of_sale:
            queryset = queryset.filter(id=point_of_sale.id)
            
        points_of_sale_data = []
        for pos in queryset:
            # Calculer les statistiques pour chaque point de vente
            total_products = pos.products.count()
            total_orders = pos.orders.filter(date_filter).count()
            total_sales = pos.orders.filter(date_filter).aggregate(
                total=Sum('total')
            )['total'] or 0
            
            points_of_sale_data.append({
                'id': pos.id,
                'name': pos.name,
                'owner': pos.owner,
                'type': pos.type,
                'status': pos.status,
                'region': pos.region,
                'commune': pos.commune,
                'total_products': total_products,
                'total_orders': total_orders,
                'total_sales': float(total_sales),
                'monthly_orders': pos.monthly_orders,
                'turnover': float(pos.turnover),
                'evaluation_score': pos.evaluation_score,
            })
            
        return {
            'summary': {
                'total_points_of_sale': queryset.count(),
                'active_points_of_sale': queryset.filter(status='actif').count(),
                'total_turnover': sum(item['turnover'] for item in points_of_sale_data),
                'average_evaluation': sum(item['evaluation_score'] for item in points_of_sale_data) / len(points_of_sale_data) if points_of_sale_data else 0
            },
            'points_of_sale': points_of_sale_data,
            'by_type': list(queryset.values('type').annotate(count=Count('id'))),
            'by_region': list(queryset.values('region').annotate(count=Count('id'))),
        }

    def _generate_sales_report(self, date_filter, point_of_sale, category):
        # Implémentation du rapport des ventes
        sales_data = Sale.objects.filter(date_filter)
        
        if point_of_sale:
            sales_data = sales_data.filter(vendor__point_of_sale=point_of_sale)
            
        if category:
            sales_data = sales_data.filter(product_variant__product__category=category)
            
        total_sales = sales_data.aggregate(
            total_amount=Sum('total_amount'),
            total_quantity=Sum('quantity')
        )
        
        sales_by_product = sales_data.values(
            'product_variant__product__name',
            'product_variant__product__category__name'
        ).annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum('total_amount')
        ).order_by('-total_revenue')
        
        return {
            'summary': {
                'total_sales': float(total_sales['total_amount'] or 0),
                'total_quantity': total_sales['total_quantity'] or 0,
                'average_sale': float(total_sales['total_amount'] or 0) / sales_data.count() if sales_data.count() > 0 else 0
            },
            'sales_by_product': list(sales_by_product),
            'daily_sales': list(sales_data.extra(
                {'date': "date(created_at)"}
            ).values('date').annotate(
                daily_sales=Sum('total_amount')
            ).order_by('date'))
        }

    def _generate_stocks_report(self, point_of_sale, category):
        # Implémentation du rapport des stocks
        products = Product.objects.all()
        
        if point_of_sale:
            products = products.filter(point_of_sale=point_of_sale)
            
        if category:
            products = products.filter(category=category)
            
        stock_data = []
        for product in products:
            variants = product.variants.all()
            total_stock = variants.aggregate(total=Sum('current_stock'))['total'] or 0
            min_stock = variants.aggregate(total=Sum('min_stock'))['total'] or 0
            max_stock = variants.aggregate(total=Sum('max_stock'))['total'] or 0
            
            stock_data.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'category': product.category.name if product.category else 'N/A',
                'supplier': product.supplier.name if product.supplier else 'N/A',
                'point_of_sale': product.point_of_sale.name,
                'status': product.status,
                'total_stock': total_stock,
                'min_stock': min_stock,
                'max_stock': max_stock,
                'variants_count': variants.count(),
            })
            
        return {
            'summary': {
                'total_products': products.count(),
                'total_stock': sum(item['total_stock'] for item in stock_data),
                'low_stock_products': len([item for item in stock_data if item['total_stock'] <= item['min_stock']]),
                'out_of_stock_products': len([item for item in stock_data if item['total_stock'] == 0]),
            },
            'products': stock_data,
            'by_category': list(products.values('category__name').annotate(
                count=Count('id'),
                total_stock=Sum('variants__current_stock')
            )),
        }

    def _generate_orders_report(self, date_filter, point_of_sale):
        # Implémentation du rapport des commandes
        orders = Order.objects.filter(date_filter)
        
        if point_of_sale:
            orders = orders.filter(point_of_sale=point_of_sale)
            
        orders_data = []
        for order in orders:
            items_count = order.items.count()
            orders_data.append({
                'id': order.id,
                'customer': order.customer.user.get_full_name() or order.customer.user.username,
                'point_of_sale': order.point_of_sale.name,
                'status': order.status,
                'total': float(order.total),
                'date': order.date,
                'delivery_date': order.delivery_date,
                'priority': order.priority,
                'items_count': items_count,
            })
            
        return {
            'summary': {
                'total_orders': orders.count(),
                'total_amount': float(orders.aggregate(total=Sum('total'))['total'] or 0),
                'average_order_value': float(orders.aggregate(total=Sum('total'))['total'] or 0) / orders.count() if orders.count() > 0 else 0,
                'pending_orders': orders.filter(status='pending').count(),
                'delivered_orders': orders.filter(status='delivered').count(),
            },
            'orders': orders_data,
            'by_status': list(orders.values('status').annotate(count=Count('id'), total=Sum('total'))),
            'by_priority': list(orders.values('priority').annotate(count=Count('id'))),
        }

    def _generate_vendors_report(self, date_filter, point_of_sale):
        # Implémentation du rapport des vendeurs ambulants
        vendors = MobileVendor.objects.all()
        
        if point_of_sale:
            vendors = vendors.filter(point_of_sale=point_of_sale)
            
        vendors_data = []
        for vendor in vendors:
            total_sales = vendor.sales_vendors.filter(date_filter).aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            
            vendors_data.append({
                'id': vendor.id,
                'full_name': vendor.full_name,
                'point_of_sale': vendor.point_of_sale.name,
                'status': vendor.status,
                'vehicle_type': vendor.vehicle_type,
                'zones': vendor.zones,
                'performance': vendor.performance,
                'average_daily_sales': float(vendor.average_daily_sales),
                'total_sales': float(total_sales),
                'total_activities': vendor.activities.count(),
            })
            
        return {
            'summary': {
                'total_vendors': vendors.count(),
                'active_vendors': vendors.filter(status='actif').count(),
                'total_sales': float(sum(item['total_sales'] for item in vendors_data)),
                'average_performance': sum(item['performance'] for item in vendors_data) / len(vendors_data) if vendors_data else 0,
            },
            'vendors': vendors_data,
            'by_status': list(vendors.values('status').annotate(count=Count('id'))),
            'by_vehicle': list(vendors.values('vehicle_type').annotate(count=Count('id'))),
        }

    def _generate_purchases_report(self, date_filter, point_of_sale):
        # Implémentation du rapport des clients/achats
        purchases = Purchase.objects.filter(date_filter)
        
        if point_of_sale:
            purchases = purchases.filter(vendor__point_of_sale=point_of_sale)
            
        purchases_data = []
        for purchase in purchases:
            purchases_data.append({
                'id': purchase.id,
                'full_name': purchase.full_name,
                'vendor': purchase.vendor.full_name,
                'zone': purchase.zone,
                'amount': float(purchase.amount),
                'purchase_date': purchase.purchase_date,
                'base': purchase.base,
                'pushcard_type': purchase.pushcard_type,
            })
            
        return {
            'summary': {
                'total_purchases': purchases.count(),
                'total_amount': float(purchases.aggregate(total=Sum('amount'))['total'] or 0),
                'average_purchase': float(purchases.aggregate(total=Sum('amount'))['total'] or 0) / purchases.count() if purchases.count() > 0 else 0,
            },
            'purchases': purchases_data,
            'by_zone': list(purchases.values('zone').annotate(
                count=Count('id'), 
                total=Sum('amount')
            )),
        }

    def _generate_performance_report(self, date_filter, point_of_sale):
        # Rapport de performance global
        return {
            'points_of_sale': self._generate_points_of_sale_report(date_filter, point_of_sale),
            'sales': self._generate_sales_report(date_filter, point_of_sale, None),
            'orders': self._generate_orders_report(date_filter, point_of_sale),
            'vendors': self._generate_vendors_report(date_filter, point_of_sale),
        }

    def _generate_file(self, report_data, report_type, format_type):
        if format_type == 'excel':
            return self._generate_excel_file(report_data, report_type)
        else:  # PDF
            return self._generate_pdf_file(report_data, report_type)

    def _generate_excel_file(self, report_data, report_type):
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Créer différentes feuilles selon le type de rapport
            if 'summary' in report_data:
                summary_df = pd.DataFrame([report_data['summary']])
                summary_df.to_excel(writer, sheet_name='Résumé', index=False)
                
            # Ajouter d'autres feuilles selon la structure des données
            for key, data in report_data.items():
                if key != 'summary' and isinstance(data, list) and data:
                    df = pd.DataFrame(data)
                    df.to_excel(writer, sheet_name=key.capitalize(), index=False)
        
        output.seek(0)
        return output

    def _generate_pdf_file(self, report_data, report_type):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Titre
        title = Paragraph(f"Rapport {report_type}", styles['Title'])
        story.append(title)
        
        # Résumé
        if 'summary' in report_data:
            summary_data = [['Métrique', 'Valeur']]
            for key, value in report_data['summary'].items():
                summary_data.append([key.replace('_', ' ').title(), str(value)])
            
            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(summary_table)
        
        doc.build(story)
        buffer.seek(0)
        return buffer

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        report = self.get_object()
        if report.file:
            response = HttpResponse(report.file.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{report.title}.{report.format}"'
            return response
        return Response({'error': 'Fichier non disponible'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        # Données pour le tableau de bord
        today = timezone.now().date()
        last_month = today - timedelta(days=30)
        
        # Statistiques générales
        total_sales = Sale.objects.aggregate(total=Sum('total_amount'))['total'] or 0
        total_orders = Order.objects.count()
        total_products = Product.objects.count()
        total_vendors = MobileVendor.objects.count()
        total_points_of_sale = PointOfSale.objects.count()
        
        # Rapports par type
        reports_by_type = Report.objects.values('report_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Activité récente (30 derniers jours)
        recent_reports = Report.objects.filter(
            created_at__date__gte=last_month
        ).values('created_at__date').annotate(
            generated=Count('id')
        ).order_by('created_at__date')
        
        # Derniers rapports générés
        latest_reports = Report.objects.all()[:10].values(
            'id', 'title', 'report_type', 'point_of_sale__name', 
            'start_date', 'end_date', 'size', 'created_at'
        )
        
        dashboard_data = {
            'total_sales': float(total_sales),
            'total_orders': total_orders,
            'total_products': total_products,
            'total_vendors': total_vendors,
            'total_points_of_sale': total_points_of_sale,
            'reports_by_type': list(reports_by_type),
            'recent_activity': list(recent_reports),
            'recent_reports': list(latest_reports),
        }
        
        serializer = DashboardSerializer(dashboard_data)
        return Response(serializer.data)