# views.py corrigé
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Count, Avg, Q, Sum, F, FloatField
from django.db.models.functions import TruncDate, Cast
from django.db import connection
from .models import PointOfSale, Agent, Photo, AgentPerformance
from .serializerss import (
    PointOfSaleListSerializer, PointOfSaleDetailSerializer, 
    PointOfSaleCreateSerializer, AgentSerializer, 
    DashboardStatsSerializer, CommuneStatsSerializer
)
from datetime import datetime, timedelta


class PointOfSaleViewSet(viewsets.ModelViewSet):
    """ViewSet pour les points de vente"""
    queryset = PointOfSale.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PointOfSaleListSerializer
        elif self.action == 'create':
            return PointOfSaleCreateSerializer
        return PointOfSaleDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtres
        commune = self.request.query_params.get('commune')
        branding = self.request.query_params.get('branding')
        potentiel = self.request.query_params.get('potentiel')
        type_pdv = self.request.query_params.get('type')
        agent_id = self.request.query_params.get('agent')
        
        if commune and commune != 'Toutes':
            queryset = queryset.filter(commune=commune)
        if branding and branding != 'Tous':
            queryset = queryset.filter(brander=(branding == 'Brandé'))
        if potentiel and potentiel != 'Tous':
            queryset = queryset.filter(potentiel=potentiel)
        if type_pdv and type_pdv != 'Tous':
            queryset = queryset.filter(type=type_pdv)
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques globales"""
        queryset = self.get_queryset()
        total = queryset.count()
        
        brandes = queryset.filter(brander=True).count()
        non_brandes = total - brandes
        premium = queryset.filter(score_global__gte=85).count()
        
        # Éligibles branding (non brandés avec bons scores)
        eligibles_branding = queryset.filter(
            brander=False,
            score_global__gte=70,
            visibilite__gte=70,
            accessibilite__gte=65
        ).count()
        
        gps_valides = queryset.filter(gps_valid=True).count()
        
        # Calcul des moyennes avec gestion SQLite
        score_moyen = self._safe_avg(queryset, 'score_global')
        score_a_moyen = self._safe_avg(queryset, 'score_a')
        score_d_moyen = self._safe_avg(queryset, 'score_d')
        score_e_moyen = self._safe_avg(queryset, 'score_e')
        
        stats = {
            'total': total,
            'brandes': brandes,
            'non_brandes': non_brandes,
            'premium': premium,
            'eligibles_branding': eligibles_branding,
            'gps_valides': gps_valides,
            'score_moyen': score_moyen,
            'score_a_moyen': score_a_moyen,
            'score_d_moyen': score_d_moyen,
            'score_e_moyen': score_e_moyen,
        }
        
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)
    
    def _safe_avg(self, queryset, field):
        """Calcule la moyenne de manière sécurisée pour SQLite"""
        try:
            result = queryset.aggregate(avg=Avg(field))['avg']
            return round(result) if result else 0
        except Exception:
            # Fallback: calcul manuel pour SQLite
            values = list(queryset.values_list(field, flat=True))
            if values:
                return round(sum(values) / len(values))
            return 0
    
    @action(detail=False, methods=['get'])
    def stats_by_commune(self, request):
        """Statistiques groupées par commune"""
        queryset = self.get_queryset()
        
        # Récupérer toutes les communes distinctes
        communes = queryset.values_list('commune', flat=True).distinct()
        
        result = []
        for commune in communes:
            commune_queryset = queryset.filter(commune=commune)
            total = commune_queryset.count()
            
            if total == 0:
                continue
            
            brandes = commune_queryset.filter(brander=True).count()
            non_brandes = total - brandes
            premium = commune_queryset.filter(score_global__gte=85).count()
            
            # Calcul des moyennes manuelles pour SQLite
            score_moyen = self._manual_avg(commune_queryset, 'score_global')
            visibilite_moyen = self._manual_avg(commune_queryset, 'visibilite')
            accessibilite_moyen = self._manual_avg(commune_queryset, 'accessibilite')
            affluence_moyen = self._manual_avg(commune_queryset, 'affluence')
            digitalisation_moyen = self._manual_avg(commune_queryset, 'digitalisation')
            
            eligibles_branding = commune_queryset.filter(
                brander=False, score_global__gte=70,
                visibilite__gte=70, accessibilite__gte=65
            ).count()
            
            result.append({
                'commune': commune,
                'total': total,
                'brandes': brandes,
                'non_brandes': non_brandes,
                'premium': premium,
                'score_moyen': score_moyen,
                'visibilite': visibilite_moyen,
                'accessibilite': accessibilite_moyen,
                'affluence': affluence_moyen,
                'digitalisation': digitalisation_moyen,
                'eligibles_branding': eligibles_branding,
            })
        
        serializer = CommuneStatsSerializer(result, many=True)
        return Response(serializer.data)
    
    def _manual_avg(self, queryset, field):
        """Calcule la moyenne manuellement pour SQLite"""
        values = list(queryset.values_list(field, flat=True))
        if values:
            return round(sum(values) / len(values))
        return 0
    
    @action(detail=False, methods=['get'])
    def branding_vs_potential(self, request):
        """Brandés vs non brandés par niveau de potentiel"""
        queryset = self.get_queryset()
        
        levels = ['standard', 'developpement', 'fort', 'premium']
        level_labels = {
            'standard': 'Standard',
            'developpement': 'Développement',
            'fort': 'Fort potentiel',
            'premium': 'Premium'
        }
        
        result = []
        for level in levels:
            data = {
                'niveau': level_labels.get(level, level),
                'brande': queryset.filter(potentiel=level, brander=True).count(),
                'non_brande': queryset.filter(potentiel=level, brander=False).count()
            }
            result.append(data)
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def radar_data(self, request):
        """Données pour le graphique radar"""
        queryset = self.get_queryset()
        commune = request.query_params.get('commune')
        
        if commune and commune != 'Toutes':
            queryset = queryset.filter(commune=commune)
        
        if not queryset.exists():
            return Response([])
        
        # Calcul manuel des moyennes pour SQLite
        data = [
            {'axe': 'Visibilité', 'valeur': self._manual_avg(queryset, 'visibilite')},
            {'axe': 'Accessibilité', 'valeur': self._manual_avg(queryset, 'accessibilite')},
            {'axe': 'Affluence', 'valeur': self._manual_avg(queryset, 'affluence')},
            {'axe': 'Digitalisation', 'valeur': self._manual_avg(queryset, 'digitalisation')},
            {'axe': 'Score global', 'valeur': self._manual_avg(queryset, 'score_global')},
        ]
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def daily_trend(self, request):
        """Tendance journalière de collecte"""
        queryset = self.get_queryset()
        
        # Derniers 30 jours
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        
        # Pour SQLite, on utilise TruncDate
        trends = queryset.filter(
            date_collecte__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('date_collecte')
        ).values('date').annotate(
            total=Count('id')
        ).order_by('date')
        
        # Formater les résultats
        result = []
        for trend in trends:
            result.append({
                'date': trend['date'].strftime('%d/%m') if trend['date'] else '',
                'total': trend['total']
            })
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def scatter_matrix(self, request):
        """Données pour la matrice visibilité vs score"""
        queryset = self.get_queryset()[:400]
        
        data = [
            {
                'x': p.visibilite,
                'y': p.score_global,
                'z': p.accessibilite,
                'name': p.name
            }
            for p in queryset
        ]
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def opportunities(self, request):
        """Top opportunités branding"""
        queryset = self.get_queryset().filter(
            brander=False,
            score_global__gte=70
        ).order_by('-score_global')[:10]
        
        serializer = PointOfSaleListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_photos(self, request, pk=None):
        """Upload de photos pour un PDV"""
        point_of_sale = self.get_object()
        photos = request.FILES.getlist('photos')
        
        for i, photo in enumerate(photos):
            Photo.objects.create(
                point_of_sale=point_of_sale,
                image=photo,
                type=request.data.get(f'type_{i}', 'facade'),
                order=i
            )
        
        point_of_sale.photos_count = point_of_sale.photos.count()
        point_of_sale.save()
        
        return Response({'message': f'{len(photos)} photos uploadées'})


class AgentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les agents (lecture seule)"""
    queryset = Agent.objects.filter(is_active=True)
    serializer_class = AgentSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Performance détaillée d'un agent"""
        agent = self.get_object()
        
        if not hasattr(agent, 'performance'):
            AgentPerformance.objects.create(agent=agent)
        agent.performance.update_performance()
        
        pdvs = agent.points_of_sale.all()
        
        data = {
            'agent': AgentSerializer(agent).data,
            'points_of_sale': PointOfSaleListSerializer(pdvs, many=True).data,
            'recent_activity': list(pdvs.order_by('-created_at')[:10].values('name', 'commune', 'created_at'))
        }
        
        return Response(data)


class FilterOptionsViewSet(viewsets.GenericViewSet):
    """ViewSet pour les options de filtres"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def communes(self, request):
        """Liste des communes disponibles"""
        communes = PointOfSale.objects.values_list('commune', flat=True).distinct()
        return Response(list(communes))
    
    @action(detail=False, methods=['get'])
    def types(self, request):
        """Types de PDV disponibles"""
        types = [{'value': choice[0], 'label': choice[1]} for choice in PointOfSale.TYPE_CHOICES]
        return Response(types)
    
    @action(detail=False, methods=['get'])
    def potentiels(self, request):
        """Niveaux de potentiel disponibles"""
        potentiels = [{'value': choice[0], 'label': choice[1]} for choice in PointOfSale.POTENTIEL_CHOICES]
        return Response(potentiels)
    
    @action(detail=False, methods=['get'])
    def quartiers(self, request):
        """Quartiers par commune"""
        commune = request.query_params.get('commune')
        if commune:
            quartiers = PointOfSale.objects.filter(
                commune=commune, quartier__isnull=False
            ).values_list('quartier', flat=True).distinct()
        else:
            quartiers = PointOfSale.objects.values_list('quartier', flat=True).distinct()
        
        return Response(list(quartiers))


# ==================== VUES POUR LE DASHBOARD ====================

class DashboardStatsView(APIView):
    """Statistiques globales du dashboard"""
    permission_classes = [IsAuthenticated]
    
    def _manual_avg(self, queryset, field):
        """Calcule la moyenne manuellement pour SQLite"""
        values = list(queryset.values_list(field, flat=True))
        if values:
            return round(sum(values) / len(values))
        return 0
    
    def get(self, request):
        queryset = self.get_queryset(request)
        
        total = queryset.count()
        brandes = queryset.filter(brander=True).count()
        non_brandes = total - brandes
        premium = queryset.filter(score_global__gte=85).count()
        
        eligibles_branding = queryset.filter(
            brander=False,
            score_global__gte=70,
            visibilite__gte=70,
            accessibilite__gte=65
        ).count()
        
        gps_valides = queryset.filter(gps_valid=True).count()
        
        stats = {
            'total': total,
            'brandes': brandes,
            'non_brandes': non_brandes,
            'premium': premium,
            'eligibles_branding': eligibles_branding,
            'gps_valides': gps_valides,
            'score_moyen': self._manual_avg(queryset, 'score_global'),
            'score_a_moyen': self._manual_avg(queryset, 'score_a'),
            'score_d_moyen': self._manual_avg(queryset, 'score_d'),
            'score_e_moyen': self._manual_avg(queryset, 'score_e'),
        }
        
        return Response(stats)
    
    def get_queryset(self, request):
        queryset = PointOfSale.objects.all()
        
        commune = request.query_params.get('commune')
        branding = request.query_params.get('branding')
        potentiel = request.query_params.get('potentiel')
        type_pdv = request.query_params.get('type')
        
        if commune and commune != 'Toutes':
            queryset = queryset.filter(commune=commune)
        if branding and branding != 'Tous':
            queryset = queryset.filter(brander=(branding == 'Brandé'))
        if potentiel and potentiel != 'Tous':
            queryset = queryset.filter(potentiel=potentiel)
        if type_pdv and type_pdv != 'Tous':
            queryset = queryset.filter(type=type_pdv)
        
        return queryset


class StatsByCommuneView(APIView):
    """Statistiques groupées par commune"""
    permission_classes = [IsAuthenticated]
    
    def _manual_avg(self, queryset, field):
        """Calcule la moyenne manuellement pour SQLite"""
        values = list(queryset.values_list(field, flat=True))
        if values:
            return round(sum(values) / len(values))
        return 0
    
    def get(self, request):
        queryset = self.get_queryset(request)
        
        # Récupérer toutes les communes distinctes
        communes = queryset.values_list('commune', flat=True).distinct()
        
        result = []
        for commune in communes:
            commune_queryset = queryset.filter(commune=commune)
            total = commune_queryset.count()
            
            if total == 0:
                continue
            
            brandes = commune_queryset.filter(brander=True).count()
            non_brandes = total - brandes
            premium = commune_queryset.filter(score_global__gte=85).count()
            
            eligibles_branding = commune_queryset.filter(
                brander=False, score_global__gte=70,
                visibilite__gte=70, accessibilite__gte=65
            ).count()
            
            result.append({
                'commune': commune,
                'total': total,
                'brandes': brandes,
                'non_brandes': non_brandes,
                'premium': premium,
                'score_moyen': self._manual_avg(commune_queryset, 'score_global'),
                'visibilite': self._manual_avg(commune_queryset, 'visibilite'),
                'accessibilite': self._manual_avg(commune_queryset, 'accessibilite'),
                'affluence': self._manual_avg(commune_queryset, 'affluence'),
                'digitalisation': self._manual_avg(commune_queryset, 'digitalisation'),
                'eligibles_branding': eligibles_branding,
            })
        
        return Response(result)
    
    def get_queryset(self, request):
        queryset = PointOfSale.objects.all()
        
        commune = request.query_params.get('commune')
        branding = request.query_params.get('branding')
        potentiel = request.query_params.get('potentiel')
        type_pdv = request.query_params.get('type')
        
        if commune and commune != 'Toutes':
            queryset = queryset.filter(commune=commune)
        if branding and branding != 'Tous':
            queryset = queryset.filter(brander=(branding == 'Brandé'))
        if potentiel and potentiel != 'Tous':
            queryset = queryset.filter(potentiel=potentiel)
        if type_pdv and type_pdv != 'Tous':
            queryset = queryset.filter(type=type_pdv)
        
        return queryset


class BrandingVsPotentialView(APIView):
    """Brandés vs non brandés par niveau de potentiel"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        queryset = self.get_queryset(request)
        
        levels = ['standard', 'developpement', 'fort', 'premium']
        level_labels = {
            'standard': 'Standard',
            'developpement': 'Développement',
            'fort': 'Fort potentiel',
            'premium': 'Premium'
        }
        
        result = []
        for level in levels:
            data = {
                'niveau': level_labels.get(level, level),
                'brande': queryset.filter(potentiel=level, brander=True).count(),
                'non_brande': queryset.filter(potentiel=level, brander=False).count()
            }
            result.append(data)
        
        return Response(result)
    
    def get_queryset(self, request):
        queryset = PointOfSale.objects.all()
        
        commune = request.query_params.get('commune')
        type_pdv = request.query_params.get('type')
        
        if commune and commune != 'Toutes':
            queryset = queryset.filter(commune=commune)
        if type_pdv and type_pdv != 'Tous':
            queryset = queryset.filter(type=type_pdv)
        
        return queryset


class RadarDataView(APIView):
    """Données pour le graphique radar"""
    permission_classes = [IsAuthenticated]
    
    def _manual_avg(self, queryset, field):
        """Calcule la moyenne manuellement pour SQLite"""
        values = list(queryset.values_list(field, flat=True))
        if values:
            return round(sum(values) / len(values))
        return 0
    
    def get(self, request):
        queryset = PointOfSale.objects.all()
        
        commune = request.query_params.get('commune')
        if commune and commune != 'Toutes':
            queryset = queryset.filter(commune=commune)
        
        if not queryset.exists():
            return Response([])
        
        data = [
            {'axe': 'Visibilité', 'valeur': self._manual_avg(queryset, 'visibilite')},
            {'axe': 'Accessibilité', 'valeur': self._manual_avg(queryset, 'accessibilite')},
            {'axe': 'Affluence', 'valeur': self._manual_avg(queryset, 'affluence')},
            {'axe': 'Digitalisation', 'valeur': self._manual_avg(queryset, 'digitalisation')},
            {'axe': 'Score global', 'valeur': self._manual_avg(queryset, 'score_global')},
        ]
        
        return Response(data)


class DailyTrendView(APIView):
    """Tendance journalière de collecte"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        queryset = PointOfSale.objects.all()
        
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        
        trends = queryset.filter(
            date_collecte__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('date_collecte')
        ).values('date').annotate(
            total=Count('id')
        ).order_by('date')
        
        result = []
        for trend in trends:
            result.append({
                'date': trend['date'].strftime('%d/%m') if trend['date'] else '',
                'total': trend['total']
            })
        
        return Response(result)


class ScatterMatrixView(APIView):
    """Données pour la matrice visibilité vs score"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        queryset = self.get_queryset(request)[:400]
        
        data = [
            {
                'x': p.visibilite,
                'y': p.score_global,
                'z': p.accessibilite,
                'name': p.name
            }
            for p in queryset
        ]
        
        return Response(data)
    
    def get_queryset(self, request):
        queryset = PointOfSale.objects.all()
        
        commune = request.query_params.get('commune')
        branding = request.query_params.get('branding')
        potentiel = request.query_params.get('potentiel')
        type_pdv = request.query_params.get('type')
        
        if commune and commune != 'Toutes':
            queryset = queryset.filter(commune=commune)
        if branding and branding != 'Tous':
            queryset = queryset.filter(brander=(branding == 'Brandé'))
        if potentiel and potentiel != 'Tous':
            queryset = queryset.filter(potentiel=potentiel)
        if type_pdv and type_pdv != 'Tous':
            queryset = queryset.filter(type=type_pdv)
        
        return queryset


class TopOpportunitiesView(APIView):
    """Top opportunités branding"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        queryset = self.get_queryset(request).filter(
            brander=False,
            score_global__gte=70
        ).order_by('-score_global')[:10]
        
        data = [
            {
                'id': p.id,
                'name': p.name,
                'commune': p.commune,
                'quartier': p.quartier,
                'type': p.type,
                'brander': p.brander,
                'potentiel': p.potentiel,
                'score_global': p.score_global,
                'visibilite': p.visibilite,
                'accessibilite': p.accessibilite,
                'affluence': p.affluence,
                'photos_count': p.photos_count,
                'eligibilite_branding': p.eligibilite_branding,
                'latitude': p.latitude,
                'longitude': p.longitude,
                'score_a': p.score_a,
                'score_d': p.score_d,
                'score_e': p.score_e,
            }
            for p in queryset
        ]
        
        return Response(data)
    
    def get_queryset(self, request):
        queryset = PointOfSale.objects.all()
        
        commune = request.query_params.get('commune')
        type_pdv = request.query_params.get('type')
        
        if commune and commune != 'Toutes':
            queryset = queryset.filter(commune=commune)
        if type_pdv and type_pdv != 'Tous':
            queryset = queryset.filter(type=type_pdv)
        
        return queryset


class AgentsPerformanceView(APIView):
    """Performance des agents collecteurs"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        agents = Agent.objects.filter(is_active=True)
        
        data = []
        for agent in agents:
            pdvs = agent.points_of_sale.all()
            total = pdvs.count()
            
            if total > 0:
                gps_valid = pdvs.filter(gps_valid=True).count()
                complete = pdvs.filter(fiche_complete=True).count()
                total_photos = sum(p.photos_count for p in pdvs)
                
                data.append({
                    'agent': agent.code,
                    'agent_name': agent.name,
                    'total': total,
                    'gps_rate': round((gps_valid / total) * 100),
                    'complete_rate': round((complete / total) * 100),
                    'photo_avg': round(total_photos / total, 1),
                })
        
        data.sort(key=lambda x: x['total'], reverse=True)
        
        return Response(data)


class FilterOptionsView(APIView):
    """Options pour les filtres"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        communes = PointOfSale.objects.values_list('commune', flat=True).distinct().order_by('commune')
        
        types = [
            {'value': 'boutique', 'label': 'Boutique'},
            {'value': 'supermarche', 'label': 'Supermarché'},
            {'value': 'superette', 'label': 'Supérette'},
            {'value': 'epicerie', 'label': 'Épicerie'},
            {'value': 'demi_grossiste', 'label': 'Demi-Grossiste'},
            {'value': 'grossiste', 'label': 'Grossiste'},
        ]
        
        potentiels = [
            {'value': 'standard', 'label': 'Standard'},
            {'value': 'developpement', 'label': 'Développement'},
            {'value': 'fort', 'label': 'Fort potentiel'},
            {'value': 'premium', 'label': 'Premium'},
        ]
        
        return Response({
            'communes': list(communes),
            'types': types,
            'potentiels': potentiels,
        })