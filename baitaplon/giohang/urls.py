from django.urls import path
from . import views

app_name = 'giohang'

urlpatterns = [
    # URL cũ
    path('them_vao_gio_hang/', views.them_vao_gio_hang, name='them_vao_gio_hang'),
    
    # URL xem giỏ hàng
    path('gio_hang/', views.gio_hang_view, name='gio_hang_view'), 
    
    # --- URL MỚI ĐỂ QUẢN LÝ GIỎ HÀNG (TĂNG/GIẢM/XÓA) ---
    path('quan_ly_gio_hang/', views.quan_ly_gio_hang, name='quan_ly_gio_hang'),
]