from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(PointOfSale)
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
