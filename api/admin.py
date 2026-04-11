from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(Permission)
admin.site.register(Role)
admin.site.register(UserProfile)
admin.site.register(Product)
admin.site.register(StockMovement)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Dispute)
admin.site.register(Token)
admin.site.register(TokenTransaction)
admin.site.register(Notification)
admin.site.register(ProductVariant)
admin.site.register(ProductFormat)
admin.site.register(Purchase)
admin.site.register(Sale)
admin.site.register(SalePOS)
admin.site.register(Report)
admin.site.register(District)
admin.site.register(Ville)
admin.site.register(Quartier)


from .models import MobileVendor, VendorActivity, VendorPerformance

@admin.register(MobileVendor)
class MobileVendorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'point_of_sale', 'status', 'performance')
    list_filter = ('status', 'point_of_sale', 'vehicle_type')
    search_fields = ('first_name', 'last_name', 'phone')

@admin.register(VendorActivity)
class VendorActivityAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'activity_type', 'timestamp')
    list_filter = ('activity_type',)
    date_hierarchy = 'timestamp'

@admin.register(VendorPerformance)
class VendorPerformanceAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'month', 'performance_score')
    list_filter = ('month',)
    ordering = ('-month',)


from django.contrib import admin
from django.utils.html import format_html
from .models import PointOfSale, PointOfSalePhoto


class PhotoInline(admin.TabularInline):
    model = PointOfSalePhoto
    extra = 0
    fields = ['image', 'thumbnail', 'type', 'caption', 'order']
    readonly_fields = ['thumbnail_preview']

    def thumbnail_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:6px;" />', obj.image.url)
        return "—"
    thumbnail_preview.short_description = "Aperçu"


@admin.register(PointOfSale)
class PointOfSaleAdmin(admin.ModelAdmin):
    inlines = [PhotoInline]

    list_display = [
        'name', 'commune', 'type', 'status', 'potentiel',
        'score_global', 'brander', 'gps_valid', 'fiche_complete',
        'agent_name', 'created_at',
    ]
    list_filter = [
        'status', 'type', 'potentiel', 'commune', 'district',
        'brander', 'gps_valid', 'fiche_complete', 'grande_voie',
    ]
    search_fields = ['name', 'owner', 'commune', 'quartier', 'address', 'agent_name', 'marque_brander']
    readonly_fields = [
        'score_a', 'score_d', 'score_e', 'score_global',
        'eligibilite_branding', 'eligibilite_exclusivite', 'eligibilite_activation',
        'gps_valid', 'fiche_complete', 'created_at', 'updated_at',
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('Identification', {
            'fields': ('user', 'name', 'owner', 'phone', 'email', 'avatar', 'registration_date')
        }),
        ('Localisation', {
            'fields': ('address', 'commune', 'quartier', 'district', 'region', 'latitude', 'longitude')
        }),
        ('Catégorie & Statut', {
            'fields': ('type', 'status', 'potentiel', 'grande_voie')
        }),
        ('Branding', {
            'fields': ('brander', 'marque_brander', 'branding_image')
        }),
        ('Indicateurs analytiques', {
            'fields': ('visibilite', 'accessibilite', 'affluence', 'digitalisation')
        }),
        ('Scores calculés (lecture seule)', {
            'fields': ('score_a', 'score_d', 'score_e', 'score_global'),
            'classes': ('collapse',),
        }),
        ('Éligibilités (lecture seule)', {
            'fields': ('eligibilite_branding', 'eligibilite_exclusivite', 'eligibilite_activation'),
            'classes': ('collapse',),
        }),
        ('Collecte terrain', {
            'fields': ('agent_name', 'date_collecte', 'gps_valid', 'fiche_complete')
        }),
        ('Commerce', {
            'fields': ('turnover', 'monthly_turnover', 'monthly_orders', 'evaluation_score')
        }),
        ('Meta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(PointOfSalePhoto)
class PointOfSalePhotoAdmin(admin.ModelAdmin):
    list_display = ['point_of_sale', 'type', 'caption', 'order', 'preview']
    list_filter = ['type']
    search_fields = ['point_of_sale__name', 'caption']

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:50px;border-radius:4px;" />', obj.image.url)
        return "—"
    preview.short_description = "Aperçu"
