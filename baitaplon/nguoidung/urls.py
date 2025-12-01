from django.urls import path
from . import views

app_name = 'nguoidung'

urlpatterns = [
    path('dang_nhap/', views.dangnhap_view, name='dang_nhap'),
    path('dang_xuat/', views.dangxuat_view, name='dang_xuat'),
    path('dang_ky/', views.dangky_view, name='dang_ky'),

    path('profile/', views.profile_view, name='profile'),
    path('order_detail/<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('cancel_order/<int:order_id>/', views.cancel_order_view, name='cancel_order'),
    
]