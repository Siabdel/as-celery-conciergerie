# core/admin.py
from django.contrib import admin
from core.models import Agency, CustomUser
from conciergerie.models import Property
from django.contrib.auth.admin import UserAdmin
from core.mixins.admin_mixins import AgencyScopedAdminMixin, BaseAgencyAdmin
from core.models import LandingSection
from django.utils.html import format_html

@admin.register(LandingSection)
class LandingSectionAdmin(BaseAgencyAdmin):
    list_display = ("title", "is_active", "order", "icon", "image_preview")
    list_editable = ("is_active", "order")
    search_fields = ("title", "description")
    readonly_fields = ("image_preview",)
    fieldsets = (
        (None, {
            "fields": ("title", "subtitle", "description", "icon", "image")
        }),
        ("Affichage", {
            "fields": ("is_active", "order", "image_preview")
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(f'<img src="{obj.image.url}" width="120" style="border-radius:8px;" />')
        return "—"
    image_preview.short_description = "Aperçu"


class CustomUserLine(admin.TabularInline):
    model = CustomUser
    extra = 1
    can_delete = True
    fk_name = 'agency'  
    
class ProfileInline(admin.StackedInline):
    model = CustomUser
    can_delete = False
    verbose_name_plural = 'CustomUser'
    fk_name = 'user'    

class PropertyInline(admin.TabularInline):
    model = Property
    can_delete = False
    verbose_name_plural = 'Properties'
    extra = 0
    fk_name = 'agency'
    fieldsets =  (('Property Information', {
            'fields': (
                'name', 'agency',
                ('type', 'owner'),
                'price_per_night',
            )
        }),
        ('Location', {
            'fields': ('address',),
        }),
        ('Details', {
            'fields': ('capacity', 'is_active'),
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    show_change_link = True
    ordering = ('name',)
    extra = 0
    
    
#-- Agency Admin ---
@admin.register(Agency)
class AgencyAdmin(BaseAgencyAdmin):
    inlines = [CustomUserLine, PropertyInline, ]
    list_display = ('name', 'slug', 'is_active', 'created_at')
    search_fields = ('name', 'slug')
    list_filter = ('is_active',)
    list_editable = ('is_active',)
    # ne pas editer slug
    prepopulated_fields = {"slug": ("name",)}   # auto-rempli à la volée
    # si vous voulez le rendre non éditable :
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.name.lower().replace(" ", "-")
        super().save(*args, **kwargs)

#--- CustomUser Admin ---
 

from django.utils.translation import gettext_lazy as _

@admin.register(CustomUser)
class CustomUserAdmin(AgencyScopedAdminMixin, UserAdmin):
    """
    Administration personnalisée pour le modèle CustomUser.
    Étend le UserAdmin standard de Django pour inclure les champs spécifiques.
    """
    model = CustomUser
    list_display = ("username", "email", "role", "agency", "is_staff", "is_active")
    list_filter = ("role", "agency", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Informations personnelles"), {"fields": ("first_name", "last_name", "email", "phone_number", "avatar")}),
        (_("Appartenance"), {"fields": ("agency", "role")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Dates importantes"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "agency", "role", "is_staff", "is_active"),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user

        # Superadmin → voit tout
        if user.is_superuser:
            return qs

        # Admin d'agence → voit uniquement les utilisateurs de son agence
        if user.role == CustomUser.Roles.AGENCY_ADMIN and user.agency:
            return qs.filter(agency=user.agency)

        # Employé → ne voit que lui-même
        if user.role == CustomUser.Roles.EMPLOYEE:
            return qs.filter(id=user.id)

        # Owner ou autres → aucun accès par défaut
        return qs.none()
    
    