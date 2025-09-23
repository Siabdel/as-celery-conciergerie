"""
URL configuration for conciergerie project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
# urls.py (niveau projet)  
from rest_framework_simplejwt.views import (  
    TokenObtainPairView,  
    TokenRefreshView,  
    TokenVerifyView,  
)  
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


urlpatterns = [
    path('', include('services_menage.urls')),

    path("admin/", admin.site.urls),
    path('service/', include('services_menage.urls')),
    path('report/', include('slick_report.urls')),
    # SQL Explorer
    path('explorer/', include('explorer.urls')),
    # pandas Report 
    # path('pandas/', include('pandas_report.urls')),
    # fullcalendar
    # path('calendar/', include('fullcalendar.urls')),
]
# token auth & rest framework
# JWT Auth
# api/auth pour login/logout
# api/auth/registration pour creer un user
# pour obtenir un token : voici les urls
# refresh token et verify token

urlpatterns += [  
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),  
    ##
    # path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
]  

# Documentation automatique avec drf-spectacular
# https://drf-spectacular.readthedocs.io/en/latest/readme.html

urlpatterns += [
    # tes autres URLs...
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]


# Ajoutez ces lignes pour servir les fichiers média en mode développement

if settings.DEBUG:

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    #urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

    # Serve static and media files from development server
    #urlpatterns += staticfiles_urlpatterns()