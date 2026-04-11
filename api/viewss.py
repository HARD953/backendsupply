from django.db.models import Count, Avg, Q, OuterRef, Subquery
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import PointOfSale, PointOfSalePhoto
from .serializerss import (
    PointOfSaleListSerializer,
    PointOfSaleDetailSerializer,
    PointOfSaleWriteSerializer,
    PhotoSerializer,
)


class PointOfSaleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    # ─────────────────────────────────────────────────────────────────────
    # Queryset de base
    # FIX 3 : on annote photos_count_annotated pour éviter le N+1
    # ─────────────────────────────────────────────────────────────────────
    def get_queryset(self):
        qs = (
            PointOfSale.objects
            .filter(user=self.request.user)
            .prefetch_related('photos')
            .annotate(photos_count_annotated=Count('photos', distinct=True))
        )

        # ── Filtres query string ──────────────────────────────────────────
        params = self.request.query_params

        commune  = params.get('commune')
        district = params.get('district')
        region   = params.get('region')
        type_pdv = params.get('type')
        status_  = params.get('status')
        potentiel = params.get('potentiel')
        # FIX : le front envoie branding="true"/"false"
        branding  = params.get('branding')
        marque    = params.get('marque_brander')
        search    = params.get('search')

        if commune:
            qs = qs.filter(commune__iexact=commune)
        if district:
            qs = qs.filter(district__iexact=district)
        if region:
            qs = qs.filter(region__iexact=region)
        if type_pdv:
            qs = qs.filter(type=type_pdv)
        if status_:
            qs = qs.filter(status=status_)
        if potentiel:
            qs = qs.filter(potentiel=potentiel)
        if branding is not None:
            qs = qs.filter(brander=(branding.lower() == 'true'))
        if marque:
            qs = qs.filter(marque_brander__icontains=marque)
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(owner__icontains=search)
                | Q(commune__icontains=search)
                | Q(quartier__icontains=search)
                | Q(address__icontains=search)
                | Q(marque_brander__icontains=search)
            )

        return qs

    # ─────────────────────────────────────────────────────────────────────
    # Choix du serializer
    # ─────────────────────────────────────────────────────────────────────
    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return PointOfSaleWriteSerializer
        if self.action == 'retrieve':
            return PointOfSaleDetailSerializer
        return PointOfSaleListSerializer

    # ─────────────────────────────────────────────────────────────────────
    # GET /api/points-vente/{id}/   — détail avec photos[]
    # ─────────────────────────────────────────────────────────────────────
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = PointOfSaleDetailSerializer(instance, context={'request': request})
        return Response(serializer.data)

    # ─────────────────────────────────────────────────────────────────────
    # POST /api/points-vente/   — création → retourne le détail
    # ─────────────────────────────────────────────────────────────────────
    def create(self, request, *args, **kwargs):
        write_ser = PointOfSaleWriteSerializer(data=request.data, context={'request': request})
        write_ser.is_valid(raise_exception=True)
        instance = write_ser.save()
        read_ser = PointOfSaleDetailSerializer(instance, context={'request': request})
        return Response(read_ser.data, status=status.HTTP_201_CREATED)

    # ─────────────────────────────────────────────────────────────────────
    # PATCH /api/points-vente/{id}/   — mise à jour partielle → retourne le détail
    # ─────────────────────────────────────────────────────────────────────
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        write_ser = PointOfSaleWriteSerializer(
            instance, data=request.data, partial=True, context={'request': request}
        )
        write_ser.is_valid(raise_exception=True)
        updated = write_ser.save()
        read_ser = PointOfSaleDetailSerializer(updated, context={'request': request})
        return Response(read_ser.data)

    # ─────────────────────────────────────────────────────────────────────
    # GET /api/points-vente/filter-options/
    #
    # Retourne les valeurs uniques pour peupler les <select> du dashboard.
    #
    # FIX : les potentiels sont triés dans l'ordre logique
    #       standard → developpement → fort_potentiel → premium
    #       et non par ordre alphabétique.
    # ─────────────────────────────────────────────────────────────────────
    @action(detail=False, methods=['get'], url_path='filter-options')
    def filter_options(self, request):
        qs = PointOfSale.objects.filter(user=request.user)

        # Valeurs simples
        communes = sorted(
            qs.exclude(commune='').values_list('commune', flat=True).distinct()
        )
        districts = sorted(
            qs.exclude(district='').values_list('district', flat=True).distinct()
        )
        regions = sorted(
            qs.exclude(region='').values_list('region', flat=True).distinct()
        )
        marques = sorted(
            qs.filter(brander=True)
              .exclude(marque_brander='')
              .exclude(marque_brander__isnull=True)
              .values_list('marque_brander', flat=True)
              .distinct()
        )

        # Types : uniquement ceux présents dans la base, avec label lisible
        type_map = dict(PointOfSale.TYPE_CHOICES)
        types_in_db = qs.values_list('type', flat=True).distinct()
        types = [
            {'value': t, 'label': type_map.get(t, t)}
            for t in sorted(types_in_db) if t
        ]

        # FIX : potentiels dans l'ordre logique métier (pas alphabétique)
        potentiel_order = ['standard', 'developpement', 'fort_potentiel', 'premium']
        potentiel_map = dict(PointOfSale.POTENTIEL_CHOICES)
        potentiels_in_db = set(qs.values_list('potentiel', flat=True).distinct())
        potentiels = [
            {'value': p, 'label': potentiel_map.get(p, p)}
            for p in potentiel_order
            if p in potentiels_in_db
        ]

        return Response({
            'communes':  list(communes),
            'districts': list(districts),
            'regions':   list(regions),
            'marques':   list(marques),
            'types':     types,
            'potentiels': potentiels,
        })

    # ─────────────────────────────────────────────────────────────────────
    # GET /api/points-vente/agents-performance/
    #
    # Stats par agent collecteur.
    # photo_avg = nombre moyen de photos par PDV recensé par cet agent.
    # ─────────────────────────────────────────────────────────────────────
    @action(detail=False, methods=['get'], url_path='agents-performance')
    def agents_performance(self, request):
        qs = (
            PointOfSale.objects
            .filter(user=request.user)
            .exclude(agent_name__isnull=True)
            .exclude(agent_name='')
            .values('agent_name')
            .annotate(
                total=Count('id'),
                gps_ok=Count('id', filter=Q(gps_valid=True)),
                fiche_ok=Count('id', filter=Q(fiche_complete=True)),
                # Nombre total de photos pour tous les PDV de cet agent
                photo_total=Count('photos', distinct=True),
            )
            .order_by('-total')
        )

        result = []
        for row in qs:
            total = row['total']
            result.append({
                # FIX : les deux clés "agent" et "agent_name" pointent sur la même valeur
                # pour correspondre à la logique du front :
                # agent: p.agent_name || p.agent || "Agent inconnu"
                'agent':         row['agent_name'],
                'agent_name':    row['agent_name'],
                'total':         total,
                'gps_rate':      round((row['gps_ok'] / total) * 100, 1) if total else 0,
                'complete_rate': round((row['fiche_ok'] / total) * 100, 1) if total else 0,
                'photo_avg':     round(row['photo_total'] / total, 1) if total else 0,
            })

        return Response(result)

    # ─────────────────────────────────────────────────────────────────────
    # POST /api/points-vente/{id}/photos/
    # Champ attendu : "images" (fichier(s)), optionnel "type", "caption"
    # ─────────────────────────────────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='photos')
    def add_photos(self, request, pk=None):
        point = self.get_object()
        files = request.FILES.getlist('images')

        if not files:
            return Response(
                {'detail': 'Aucune image. Utilisez le champ "images".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        photo_type = request.data.get('type', 'facade')
        caption    = request.data.get('caption', '')
        current_count = point.photos.count()

        created = []
        for i, file in enumerate(files):
            photo = PointOfSalePhoto.objects.create(
                point_of_sale=point,
                image=file,
                type=photo_type,
                caption=caption,
                order=current_count + i,
            )
            created.append(photo)

        serializer = PhotoSerializer(created, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ─────────────────────────────────────────────────────────────────────
    # DELETE /api/points-vente/{id}/photos/{photo_id}/
    # ─────────────────────────────────────────────────────────────────────
    @action(detail=True, methods=['delete'], url_path='photos/(?P<photo_id>[0-9]+)')
    def delete_photo(self, request, pk=None, photo_id=None):
        point = self.get_object()
        try:
            photo = point.photos.get(pk=photo_id)
            if photo.image:
                photo.image.delete(save=False)
            if photo.thumbnail:
                photo.thumbnail.delete(save=False)
            photo.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PointOfSalePhoto.DoesNotExist:
            return Response({'detail': 'Photo introuvable.'}, status=status.HTTP_404_NOT_FOUND)

    # ─────────────────────────────────────────────────────────────────────
    # GET /api/points-vente/stats/
    # KPIs globaux pour la vue "Direction" du dashboard
    # ─────────────────────────────────────────────────────────────────────
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = PointOfSale.objects.filter(user=request.user)
        total = qs.count()

        empty = {
            'total': 0, 'brandes': 0, 'non_brandes': 0, 'actifs': 0,
            'premium': 0, 'eligibles_branding': 0, 'gps_valides': 0,
            'score_moyen': 0, 'score_a_moyen': 0, 'score_d_moyen': 0, 'score_e_moyen': 0,
        }
        if total == 0:
            return Response(empty)

        agg = qs.aggregate(
            brandes=Count('id', filter=Q(brander=True)),
            actifs=Count('id', filter=Q(status='actif')),
            premium=Count('id', filter=Q(score_global__gte=85)),
            eligibles_branding=Count('id', filter=Q(eligibilite_branding=True)),
            gps_valides=Count('id', filter=Q(gps_valid=True)),
            score_moyen=Avg('score_global'),
            score_a_moyen=Avg('score_a'),
            score_d_moyen=Avg('score_d'),
            score_e_moyen=Avg('score_e'),
        )

        return Response({
            'total':              total,
            'brandes':            agg['brandes'],
            'non_brandes':        total - agg['brandes'],
            'actifs':             agg['actifs'],
            'premium':            agg['premium'],
            'eligibles_branding': agg['eligibles_branding'],
            'gps_valides':        agg['gps_valides'],
            'score_moyen':        round(agg['score_moyen'] or 0, 1),
            'score_a_moyen':      round(agg['score_a_moyen'] or 0, 1),
            'score_d_moyen':      round(agg['score_d_moyen'] or 0, 1),
            'score_e_moyen':      round(agg['score_e_moyen'] or 0, 1),
        })