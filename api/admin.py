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
