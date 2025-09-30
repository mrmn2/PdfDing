from django.contrib import admin

from api_auth.models import AccessToken

# Register your models here.


class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'last_used', 'created')
    search_fields = ('name', 'user__username', 'user__email')
    readonly_fields = ('knox_token', 'created', 'last_used')
    list_filter = ('created', 'last_used')


admin.site.register(AccessToken, AccessTokenAdmin)
