# Dans votre fichier signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count, Sum
from django.utils import timezone
from .models import Order, PointOfSale

@receiver([post_save, post_delete], sender=Order)
def update_point_of_sale_stats(sender, instance, **kwargs):
    """
    Met à jour les statistiques du point de vente lors des modifications de commandes
    """
    point_of_sale = instance.point_of_sale
    now = timezone.now()
    
    # Commandes du mois en cours
    current_month_orders = Order.objects.filter(
        point_of_sale=point_of_sale,
        date__year=now.year,
        date__month=now.month
    )
    
    # Mise à jour du nombre de commandes mensuelles
    point_of_sale.monthly_orders = current_month_orders.count()
    
    # Calcul du score d'évaluation (exemple basé sur le statut des commandes)
    delivered_orders = current_month_orders.filter(status='delivered').count()
    total_orders = point_of_sale.monthly_orders
    
    if total_orders > 0:
        # Score basé sur le taux de livraison (vous pouvez adapter cette logique)
        point_of_sale.evaluation_score = (delivered_orders / total_orders) * 10
    else:
        point_of_sale.evaluation_score = 0.0
    
    point_of_sale.save()