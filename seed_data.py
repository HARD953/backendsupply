from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import (
    Category, Supplier, PointOfSale, Permission, Role, UserProfile,
    Product, StockMovement, Order, OrderItem
)
from decimal import Decimal
from datetime import datetime
import uuid

class Command(BaseCommand):
    help = 'Seed database with initial data'

    def handle(self, *args, **kwargs):
        # Permissions
        permissions_data = [
            {'id': 'all', 'name': 'Accès Complet', 'category': 'Système'},
            {'id': 'stock_management', 'name': 'Gestion Stocks', 'category': 'Opérations'},
            {'id': 'orders_management', 'name': 'Gestion Commandes', 'category': 'Opérations'},
        ]
        for perm in permissions_data:
            Permission.objects.get_or_create(id=perm['id'], defaults=perm)

        # Rôles
        roles_data = [
            {
                'id': 'super_admin',
                'name': 'Super Admin',
                'description': 'Accès complet à toutes les fonctionnalités',
                'color': 'bg-red-100 text-red-800 border-red-200',
                'permissions': ['all']
            },
            {
                'id': 'gestionnaire_stock',
                'name': 'Gestionnaire Stock',
                'description': 'Gestion des stocks et inventaires',
                'color': 'bg-blue-100 text-blue-800 border-blue-200',
                'permissions': ['stock_management']
            },
        ]
        for role_data in roles_data:
            permissions = role_data.pop('permissions')
            role, _ = Role.objects.get_or_create(id=role_data['id'], defaults=role_data)
            role.permissions.set(Permission.objects.filter(id__in=permissions))

        # Utilisateur
        user, _ = User.objects.get_or_create(username='k.jean', defaults={
            'email': 'k.jean@lanfiatech.com',
            'password': 'pbkdf2_sha256$390000$randomsalt$hashedpassword'  # Remplacer par un vrai mot de passe
        })
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'phone': '+225 07 12 34 56 78',
                'location': 'Abidjan, Plateau',
                'role': Role.objects.get(id='super_admin'),
                'join_date': '2024-01-15',
                'status': 'active'
            }
        )

        # Catégories
        categories_data = [
            {'name': 'Céréales', 'description': ''},
            {'name': 'Huiles', 'description': ''},
            {'name': 'Épicerie', 'description': ''},
            {'name': 'Farines', 'description': ''},
        ]
        for cat in categories_data:
            Category.objects.get_or_create(name=cat['name'], defaults={'description': cat['description']})

        # Fournisseurs
        suppliers_data = [
            {'name': 'Importateur Adjamé', 'contact': '', 'address': '', 'email': ''},
            {'name': 'Huilerie Locale', 'contact': '', 'address': '', 'email': ''},
        ]
        for sup in suppliers_data:
            Supplier.objects.get_or_create(name=sup['name'], defaults=sup)

        # Points de vente
        pos_data = [
            {
                'name': 'Supermarché Plateau',
                'owner': 'Jean Kouadio',
                'phone': '+225 07 12 34 56 78',
                'email': 'plateau@supermarket.ci',
                'address': 'Boulevard Clozel, Plateau, Abidjan',
                'latitude': 5.3197,
                'longitude': -4.0267,
                'district': 'Abidjan',
                'region': 'Abidjan',
                'commune': 'Plateau',
                'type': 'supermarche',
                'status': 'actif',
                'registration_date': '2024-01-15',
                'turnover': Decimal('2500000'),
                'monthly_orders': 45,
                'evaluation_score': 4.8
            },
        ]
        pos, _ = PointOfSale.objects.get_or_create(name=pos_data[0]['name'], defaults=pos_data[0])

        # Produits
        products_data = [
            {
                'name': 'Riz Parfumé 25kg',
                'category': Category.objects.get(name='Céréales'),
                'sku': 'RIZ-25KG-001',
                'current_stock': 45,
                'min_stock': 20,
                'max_stock': 100,
                'price': Decimal('12500'),
                'supplier': Supplier.objects.get(name='Importateur Adjamé'),
                'point_of_sale': pos,
                'description': 'Riz parfumé de qualité supérieure, origine Thaïlande',
                'status': 'en_stock'
            },
        ]
        for prod in products_data:
            Product.objects.get_or_create(sku=prod['sku'], defaults=prod)

        # Commandes
        order_data = {
            'id': 'CMD-002',
            'customer_name': 'Boutique Cocody',
            'customer_email': 'info@boutique-cocody.ci',
            'customer_phone': '+225 05 06 07 08 09',
            'customer_address': 'Cocody, Abidjan',
            'point_of_sale': pos,
            'status': 'confirmed',
            'total': Decimal('89500'),
            'date': '2024-12-14',
            'delivery_date': '2024-12-16',
            'priority': 'medium',
            'notes': ''
        }
        order, _ = Order.objects.get_or_create(id=order_data['id'], defaults=order_data)
        OrderItem.objects.get_or_create(
            order=order,
            name='Farine de Blé 50kg',
            defaults={
                'quantity': 5,
                'price': Decimal('12000'),
                'total': Decimal('60000')
            }
        )

        self.stdout.write(self.style.SUCCESS('Données initiales insérées avec succès'))
