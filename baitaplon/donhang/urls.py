from django.urls import path
from . import views

app_name = 'donhang'

urlpatterns = [
    # URL cho trang checkout
    path('checkout/', views.checkout_view, name='checkout'),
    
    # URL để xử lý việc đặt hàng (khi nhấn nút "Place Order")
    path('place_order/', views.place_order_view, name='place_order'),
    
    # URL VNPAY gọi về sau khi thanh toán
    path('vnpay_return/', views.vnpay_return_view, name='vnpay_return'),
    
    # URL trang đặt hàng thành công
    path('order_success/<int:order_id>/', views.order_success_view, name='order_success'),
]