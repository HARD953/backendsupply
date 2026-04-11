from rest_framework import serializers
from .models import PointOfSale, PointOfSalePhoto


# ─────────────────────────────────────────────────────────────────────────────
# Photo
# ─────────────────────────────────────────────────────────────────────────────

class PhotoSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = PointOfSalePhoto
        fields = ['id', 'image', 'thumbnail', 'type', 'caption', 'order']

    def _abs(self, request, url):
        if not url:
            return None
        return request.build_absolute_uri(url) if request else url

    def get_image(self, obj):
        return self._abs(self.context.get('request'), obj.image.url if obj.image else None)

    def get_thumbnail(self, obj):
        request = self.context.get('request')
        if obj.thumbnail:
            return self._abs(request, obj.thumbnail.url)
        # Fallback sur l'image principale si pas de thumbnail
        return self._abs(request, obj.image.url if obj.image else None)


# ─────────────────────────────────────────────────────────────────────────────
# Point de vente – Liste (allégé, sans photos)
# ─────────────────────────────────────────────────────────────────────────────

class PointOfSaleListSerializer(serializers.ModelSerializer):
    """
    Utilisé pour GET /api/points-vente/
    Tous les champs consommés par LanfiaLinkDashboard.tsx sont présents.

    Correspondance front → back :
      p.branding                 ← brander (bool) → transformé côté front "Brandé"/"Non brandé"
      p.potentiel_label          ← potentiel_label  [FIX 1]
      p.scoreA                   ← score_a
      p.scoreD                   ← score_d
      p.scoreE                   ← score_e
      p.score                    ← score_global
      p.caMensuel                ← monthly_turnover  [FIX 4]
      p.gpsValid                 ← gps_valid
      p.ficheComplete            ← fiche_complete
      p.eligibiliteBranding      ← eligibilite_branding
      p.eligibiliteExclusivite   ← eligibilite_exclusivite
      p.eligibiliteActivation    ← eligibilite_activation
      p.agent / p.agent_name     ← agent_name  [FIX 2]
      p.dateCollecte             ← date_collecte
      p.grandeVoie               ← grande_voie
      p.photos_count             ← photos_count  [FIX 3]
    """

    # FIX 1 — potentiel_label : "fort_potentiel" → "Fort potentiel"
    potentiel_label = serializers.SerializerMethodField()

    # FIX 2 — "agent" alias de agent_name pour satisfaire
    #          p.agent_name || p.agent || "Agent inconnu" dans le front
    agent = serializers.SerializerMethodField()

    # FIX 3 — photos_count sans N+1
    photos_count = serializers.SerializerMethodField()

    avatar = serializers.SerializerMethodField()

    class Meta:
        model = PointOfSale
        fields = [
            # Identification
            'id', 'name', 'owner', 'phone', 'email',
            'address', 'commune', 'quartier', 'district', 'region',
            # Catégorisation
            'type', 'status', 'potentiel', 'potentiel_label',
            # GPS
            'latitude', 'longitude',
            # Branding
            'brander', 'marque_brander',
            # Analytique
            'visibilite', 'accessibilite', 'affluence', 'digitalisation',
            # Scores
            'score_a', 'score_d', 'score_e', 'score_global',
            # Éligibilités
            'eligibilite_branding', 'eligibilite_exclusivite', 'eligibilite_activation',
            # Collecte
            'gps_valid', 'fiche_complete', 'grande_voie',
            'agent', 'agent_name', 'date_collecte',
            # Commerce — FIX 4 : monthly_turnover = caMensuel côté front
            'turnover', 'monthly_turnover', 'monthly_orders', 'evaluation_score',
            'registration_date',
            # Médias
            'avatar', 'photos_count',
            # Meta
            'created_at', 'updated_at',
        ]

    def get_potentiel_label(self, obj):
        """FIX 1 : label lisible du potentiel."""
        return dict(PointOfSale.POTENTIEL_CHOICES).get(obj.potentiel, 'Standard')

    def get_agent(self, obj):
        """FIX 2 : alias de agent_name sous la clé 'agent'."""
        return obj.agent_name or ''

    def get_photos_count(self, obj):
        """
        FIX 3 : utilise l'annotation si disponible (via annotate dans la vue),
        sinon compte via le related manager (safe avec prefetch_related).
        """
        if hasattr(obj, 'photos_count_annotated'):
            return obj.photos_count_annotated
        return obj.photos.count()

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            url = obj.avatar.url
            return request.build_absolute_uri(url) if request else url
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Point de vente – Détail complet avec photos[]
# Utilisé pour GET /api/points-vente/{id}/  (lightbox dashboard)
# ─────────────────────────────────────────────────────────────────────────────

class PointOfSaleDetailSerializer(PointOfSaleListSerializer):
    photos = PhotoSerializer(many=True, read_only=True)
    branding_image = serializers.SerializerMethodField()

    class Meta(PointOfSaleListSerializer.Meta):
        fields = PointOfSaleListSerializer.Meta.fields + ['photos', 'branding_image']

    def get_branding_image(self, obj):
        request = self.context.get('request')
        if obj.branding_image:
            url = obj.branding_image.url
            return request.build_absolute_uri(url) if request else url
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Point de vente – Écriture (création / mise à jour)
# Accepte multipart/form-data pour les images
# ─────────────────────────────────────────────────────────────────────────────

class PointOfSaleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointOfSale
        fields = [
            'name', 'owner', 'phone', 'email', 'address',
            'commune', 'quartier', 'district', 'region',
            'type', 'status', 'potentiel',
            'latitude', 'longitude',
            'brander', 'marque_brander', 'branding_image', 'avatar',
            'visibilite', 'accessibilite', 'affluence', 'digitalisation',
            'grande_voie', 'agent_name', 'date_collecte',
            'turnover', 'monthly_turnover', 'monthly_orders', 'evaluation_score',
            'registration_date',
        ]

    def validate(self, data):
        if data.get('brander') and not data.get('marque_brander'):
            raise serializers.ValidationError({
                'marque_brander': "La marque est obligatoire si le PDV est brandé."
            })
        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# ─────────────────────────────────────────────────────────────────────────────
# Performance agents
# ─────────────────────────────────────────────────────────────────────────────

class AgentPerformanceSerializer(serializers.Serializer):
    agent = serializers.CharField()
    agent_name = serializers.CharField()
    total = serializers.IntegerField()
    gps_rate = serializers.FloatField()
    complete_rate = serializers.FloatField()
    photo_avg = serializers.FloatField()