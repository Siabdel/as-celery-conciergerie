from django.contrib import admin
from core.models import Agency, UserProfile
from conciergerie.models import Property



class UserProfileLine(admin.TabularInline):
    model = UserProfile
    extra = 1
    can_delete = True
    fk_name = 'agency'  
    
class ProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'UserProfile'
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
class AgencyAdmin(admin.ModelAdmin):
    inlines = [UserProfileLine, PropertyInline, ]
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

#--- UserProfile Admin ---
    
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'agency')
    search_fields = ('user__username', 'user__email', 'agency__name')
    list_filter = ('agency',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        # Employee → profils de son agence
        if hasattr(request.user, "employee"):
            return qs.filter(user__employee__agency=request.user.employee.agency)

        # Owner → on peut lui montrer **rien** (ou ses propres profils s’il en a)
        # Ici : **rien** (liste vide)
        return qs.none()