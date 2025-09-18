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
            delivered_orders_ca = current_month_orders.all()
            delivered_orders = current_month_orders.filter(status='delivered')
            
            # Mise à jour du nombre de commandes mensuelles
            monthly_orders_count = current_month_orders.count()
            
            # Mise à jour du chiffre d'affaires (seulement les commandes livrées)
            ca_data = delivered_orders_ca.aggregate(total_ca=Sum('total'))
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


# signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import Sale

@receiver(pre_save, sender=Sale)
def valider_vente_avant_sauvegarde(sender, instance, **kwargs):
    print(f"🔵 Signal pre_save déclenché pour Sale #{instance.id if instance.id else 'Nouveau'}")
    
    if instance.vendor_activity:
        print(f"   Activité vendeur: {instance.vendor_activity.id}")
        print(f"   Quantité demandée: {instance.quantity}")
        print(f"   Ventes actuelles: {instance.vendor_activity.quantity_sales}")
        print(f"   Quantité assignée: {instance.vendor_activity.quantity_assignes}")
        print(f"   Peut vendre: {instance.vendor_activity.peut_vendre(instance.quantity)}")
        
        if not instance.vendor_activity.peut_vendre(instance.quantity):
            raise ValidationError(
                f"Impossible de vendre {instance.quantity} unités. "
                f"Quantité restante: {instance.vendor_activity.quantite_restante()}"
            )
    else:
        print("   ⚠️ Aucune activité vendeur associée")

@receiver(post_save, sender=Sale)
def incrementer_ventes_apres_sauvegarde(sender, instance, created, **kwargs):
    print(f"🟢 Signal post_save déclenché pour Sale #{instance.id}")
    print(f"   Créé: {created}")
    
    if created and instance.vendor_activity:
        print(f"   Tentative d'incrémenter les ventes de {instance.quantity}")
        try:
            from .models import VendorActivity
            activity = VendorActivity.objects.get(id=instance.vendor_activity.id)
            activity.incrementer_ventes(instance.quantity)
            print(f"   ✅ Ventes incrémentées avec succès")
        except ValidationError as e:
            print(f"   ❌ Erreur: {e}")
            instance.delete()
            raise e
    else:
        print("   ⏭️ Aucune action nécessaire")