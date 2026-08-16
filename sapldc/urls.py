from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('portal.urls')),
    path('api/', include('sapldc.api_urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'SAPL-DC — Câmara Municipal de Duque de Caxias'
admin.site.site_title = 'SAPL-DC'
admin.site.index_title = 'Administração do Processo Legislativo'
