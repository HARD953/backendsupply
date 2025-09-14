# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from django.utils import timezone
from .models import Order, PointOfSale

@receiver([post_save, post_delete], sender=Order)
def update_point_of_sale_stats(sender, instance, **kwargs):
    """
    Met à jour les statistiques du point de vente lors des modifications de commandes
    """
    point_of_sale = instance.point_of_sale
    now = timezone.now()
    
    # Commandes du mois en cours avec statut livré
    current_month_orders = Order.objects.filter(
        point_of_sale=point_of_sale,
        date__year=now.year,
        date__month=now.month
    )
    
    # Commandes livrées du mois en cours
    delivered_orders = current_month_orders.filter(status='delivered')
    
    # Mise à jour du nombre de commandes mensuelles
    point_of_sale.monthly_orders = current_month_orders.count()
    
    # Mise à jour du chiffre d'affaires (seulement les commandes livrées)
    ca_data = delivered_orders.aggregate(total_ca=Sum('total'))
    point_of_sale.turnover = ca_data['total_ca'] or 0.00
    
    # Calcul du score d'évaluation (basé sur le taux de livraison)
    total_orders_count = current_month_orders.count()
    delivered_orders_count = delivered_orders.count()
    
    if total_orders_count > 0:
        point_of_sale.evaluation_score = (delivered_orders_count / total_orders_count) * 10
    else:
        point_of_sale.evaluation_score = 0.0
    
    point_of_sale.save()