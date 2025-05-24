"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenRefreshView

schema_view = get_schema_view(
    openapi.Info(
        title="Omni",
        default_version='v1',),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('Usuario.urls')),
    path('api/', include('Permissao.urls')),
    path('api/', include('Agente.urls')),
    path('api/', include('Chat.urls')),
    path('api/', include('Contexto.urls')),
    path('api/', include('Modelo.urls')),
    path('api/', include('Dashboard.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),     
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0),name='swagger-ui'),
]
