# serializers.py
from rest_framework import serializers
from .models import PointOfSale, Agent, Photo, AgentPerformance, EvaluationHistory, Activation

class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['id', 'image', 'thumbnail', 'type', 'caption', 'order']


class PointOfSaleListSerializer(serializers.ModelSerializer):
    """Sérializer pour la liste (champs réduits)"""
    potentiel_label = serializers.SerializerMethodField()
    eligibilite_branding = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PointOfSale
        fields = [
            'id', 'name', 'commune', 'quartier', 'type', 
            'brander', 'potentiel', 'potentiel_label', 'score_global',
            'visibilite', 'accessibilite', 'affluence', 'photos_count',
            'eligibilite_branding', 'latitude', 'longitude'
        ]
    
    def get_potentiel_label(self, obj):
        labels = {
            'premium': 'Premium stratégique',
            'fort': 'Fort potentiel',
            'developpement': 'Développement',
            'standard': 'Standard'
        }
        return labels.get(obj.potentiel, 'Standard')


class PointOfSaleDetailSerializer(serializers.ModelSerializer):
    """Sérializer pour le détail complet"""
    photos = PhotoSerializer(many=True, read_only=True)
    potentiel_label = serializers.SerializerMethodField()
    eligibilite_branding = serializers.BooleanField(read_only=True)
    eligibilite_exclusivite = serializers.BooleanField(read_only=True)
    eligibilite_activation = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PointOfSale
        fields = '__all__'
        depth = 1
    
    def get_potentiel_label(self, obj):
        labels = {
            'premium': 'Premium stratégique',
            'fort': 'Fort potentiel',
            'developpement': 'Développement',
            'standard': 'Standard'
        }
        return labels.get(obj.potentiel, 'Standard')


class PointOfSaleCreateSerializer(serializers.ModelSerializer):
    """Sérializer pour la création"""
    class Meta:
        model = PointOfSale
        exclude = ['score_a', 'score_d', 'score_e', 'score_global', 'potentiel', 'fiche_complete']


class AgentSerializer(serializers.ModelSerializer):
    performance = serializers.SerializerMethodField()
    
    class Meta:
        model = Agent
        fields = ['id', 'code', 'name', 'email', 'phone', 'avatar', 'is_active', 'performance']
    
    def get_performance(self, obj):
        if hasattr(obj, 'performance'):
            return {
                'total_collecte': obj.performance.total_collecte,
                'gps_rate': obj.performance.gps_rate,
                'complete_rate': obj.performance.complete_rate,
                'photo_avg': obj.performance.photo_avg
            }
        return None


class DashboardStatsSerializer(serializers.Serializer):
    """Sérializer pour les statistiques du dashboard"""
    total = serializers.IntegerField()
    brandes = serializers.IntegerField()
    non_brandes = serializers.IntegerField()
    premium = serializers.IntegerField()
    eligibles_branding = serializers.IntegerField()
    gps_valides = serializers.IntegerField()
    score_moyen = serializers.IntegerField()
    score_a_moyen = serializers.IntegerField()
    score_d_moyen = serializers.IntegerField()
    score_e_moyen = serializers.IntegerField()


class CommuneStatsSerializer(serializers.Serializer):
    """Statistiques par commune"""
    commune = serializers.CharField()
    total = serializers.IntegerField()
    brandes = serializers.IntegerField()
    non_brandes = serializers.IntegerField()
    premium = serializers.IntegerField()
    score_moyen = serializers.IntegerField()
    visibilite = serializers.IntegerField()
    accessibilite = serializers.IntegerField()
    affluence = serializers.IntegerField()
    digitalisation = serializers.IntegerField()
    eligibles_branding = serializers.IntegerField()


class BrandingPotentialSerializer(serializers.Serializer):
    """Brandés vs non brandés par niveau de potentiel"""
    niveau = serializers.CharField()
    brande = serializers.IntegerField()
    non_brande = serializers.IntegerField()