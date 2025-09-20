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

# # signals.py
# from django.db.models.signals import pre_save, post_save
# from django.dispatch import receiver
# from django.core.exceptions import ValidationError
# from .models import Sale, VendorActivity
# import logging

# logger = logging.getLogger(__name__)

# @receiver(pre_save, sender=Sale)
# def valider_vente_avant_sauvegarde(sender, instance, **kwargs):
#     """
#     Validation stricte avant sauvegarde d'une vente
#     """
#     if instance.vendor_activity:
#         # Recharger l'activité pour avoir les données les plus récentes
#         try:
#             fresh_activity = VendorActivity.objects.get(id=instance.vendor_activity.id)
#         except VendorActivity.DoesNotExist:
#             raise ValidationError("L'activité de vendeur associée n'existe pas")
        
#         # Vérifier la cohérence de l'activité
#         if not fresh_activity.verifier_coherence():
#             logger.warning(f"Incohérence détectée dans l'activité {fresh_activity.id}")
#             fresh_activity.corriger_quantite_restante()
#             fresh_activity.refresh_from_db()
        
#         # Validation principale
#         if instance.quantity > fresh_activity.quantity_restante:
#             raise ValidationError(
#                 f"Impossible de vendre {instance.quantity} unités. "
#                 f"Quantité restante: {fresh_activity.quantity_restante}"
#             )
        
#         # Validation quantité positive
#         if instance.quantity <= 0:
#             raise ValidationError("La quantité de vente doit être positive")
        
#         print(f"✅ Validation vente OK: {instance.quantity} unités sur {fresh_activity.quantity_restante} disponibles")

# @receiver(post_save, sender=Sale)
# def incrementer_ventes_apres_sauvegarde(sender, instance, created, **kwargs):
#     """
#     Incrémentation automatique des ventes après sauvegarde
#     """
#     if created and instance.vendor_activity:
#         try:
#             # Recharger pour éviter les problèmes de cache
#             fresh_activity = VendorActivity.objects.get(id=instance.vendor_activity.id)
            
#             # Incrémenter les ventes
#             fresh_activity.incrementer_ventes(instance.quantity)
            
#             logger.info(
#                 f"Vente enregistrée: {instance.quantity} unités "
#                 f"pour l'activité {fresh_activity.id}"
#             )
            
#         except VendorActivity.DoesNotExist:
#             logger.error(f"Activité {instance.vendor_activity.id} introuvable lors de l'incrémentation")
#         except ValidationError as e:
#             logger.error(f"Erreur lors de l'incrémentation des ventes: {e}")
#             # On ne re-raise pas l'erreur ici car la vente est déjà sauvegardée
#             # Mais on pourrait implémenter une logique de rollback si nécessaire
#         except Exception as e:
#             logger.error(f"Erreur inattendue lors de l'incrémentation: {e}")

# # Signal optionnel pour debug
# @receiver(post_save, sender=VendorActivity)
# def debug_vendor_activity_save(sender, instance, created, **kwargs):
#     """
#     Debug: Log les informations après sauvegarde d'une activité
#     """
#     if created:
#         print(f"🆕 Nouvelle activité créée:")
#         print(f"   ID: {instance.id}")
#         print(f"   Type: {instance.activity_type}")
#         print(f"   Quantité assignée: {instance.quantity_assignes}")
#         print(f"   Quantité restante: {instance.quantity_restante}")
#         print(f"   Commande liée: {instance.related_order.id if instance.related_order else 'Aucune'}")
        
#         # Vérification de cohérence
#         if not instance.verifier_coherence():
#             logger.warning(f"Incohérence détectée dans la nouvelle activité {instance.id}")
#     else:
#         print(f"📝 Activité {instance.id} mise à jour:")
#         print(f"   Quantité restante: {instance.quantity_restante}")
#         print(f"   Ventes: {instance.quantity_sales}")