# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from django.utils import timezone
from django.db import transaction
from .models import Order, PointOfSale

@receiver([post_save, post_delete], sender=Order)
def update_point_of_sale_stats(sender, instance, **kwargs):
    """
    Met à jour les statistiques du point de vente lors des modifications de commandes
    """
    try:
        point_of_sale = instance.point_of_sale
        now = timezone.now()
        
        # Utiliser une transaction pour éviter les incohérences
        with transaction.atomic():
            # Commandes du mois en cours
            current_month_orders = Order.objects.filter(
                point_of_sale=point_of_sale,
                date__year=now.year,
                date__month=now.month
            )
            
            # Commandes livrées du mois en cours
            delivered_orders = current_month_orders.filter(status='delivered')
            
            # Mise à jour du nombre de commandes mensuelles
            monthly_orders_count = current_month_orders.count()
            
            # Mise à jour du chiffre d'affaires (seulement les commandes livrées)
            ca_data = delivered_orders.aggregate(total_ca=Sum('total'))
            turnover_value = ca_data['total_ca'] if ca_data['total_ca'] is not None else 0.00
            
            # Calcul du score d'évaluation
            delivered_orders_count = delivered_orders.count()
            evaluation_score_value = 0.0
            
            if monthly_orders_count > 0:
                evaluation_score_value = (delivered_orders_count / monthly_orders_count) * 10
            
            # Mise à jour de l'instance
            PointOfSale.objects.filter(id=point_of_sale.id).update(
                monthly_orders=monthly_orders_count,
                turnover=turnover_value,
                evaluation_score=evaluation_score_value,
                updated_at=timezone.now()
            )
            
    except Exception as e:
        # Loguer l'erreur mais ne pas bloquer l'application
        print(f"Erreur lors de la mise à jour des stats du point de vente: {e}")