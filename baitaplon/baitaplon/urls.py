from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('quanly/', include('quanly.urls')),
    path('', include('trangchu.urls')),
    path('sanpham/', include('sanpham.urls')),
    path('nguoidung/', include('nguoidung.urls')),
    path('giohang/', include('giohang.urls')),
    path('', include('core.urls')),     
    path('donhang/', include('donhang.urls')),

]

if settings.DEBUG:
    # Media files (uploaded images)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Static files (CSS, JS) - chỉ serve khi DEBUG=True
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
