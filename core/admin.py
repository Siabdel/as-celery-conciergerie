from django.contrib import admin
from core.models import Agency, UserProfile


#-- Agency Admin ---
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    search_fields = ('name', 'slug')
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}   
    list_editable = ('is_active',)
    # ne pas editer slug
    prepopulated_fields = {"slug": ("name",)}   # auto-rempli à la volée
    # si vous voulez le rendre non éditable :
    readonly_fields = ("slug",)
    
    
    
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.name.lower().replace(" ", "-")
        super().save(*args, **kwargs)

#--- UserProfile Admin ---
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'agency', 'role', 'phone_number')
    search_fields = ('user__username', 'user__email', 'agency__name')
    list_filter = ('role', 'agency') 
    def save(self, *args, **kwargs):
        if not self.role:
            self.role = 'staff'
        super().save(*args, **kwargs)
        
        
# Register your models here.
admin.site.register(Agency)
admin.site.register(UserProfile)
