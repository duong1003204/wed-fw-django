from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import DonHang
from sanpham.models import BienTheSanPham


def giam_so_luong_san_pham(don_hang):
    """Hàm helper để giảm số lượng sản phẩm khi đơn hàng được đánh dấu 'đã giao'"""
    chi_tiet_list = don_hang.chi_tiet.all()
    
    for chi_tiet in chi_tiet_list:
        # Tìm biến thể sản phẩm phù hợp với size và color
        if chi_tiet.size and chi_tiet.color:
            # Tìm biến thể có size và color khớp
            bien_the = BienTheSanPham.objects.filter(
                ma_san_pham=chi_tiet.ma_san_pham,
                kich_thuoc=chi_tiet.size,
                mau_sac=chi_tiet.color
            ).first()
        else:
            # Nếu không có size/color, tìm biến thể đầu tiên
            bien_the = BienTheSanPham.objects.filter(
                ma_san_pham=chi_tiet.ma_san_pham
            ).first()
        
        if bien_the:
            # Giảm số lượng, đảm bảo không âm
            if bien_the.so_luong >= chi_tiet.so_luong:
                bien_the.so_luong -= chi_tiet.so_luong
            else:
                bien_the.so_luong = 0
            bien_the.save()


@receiver(pre_save, sender=DonHang)
def giam_so_luong_san_pham_khi_da_giao(sender, instance, **kwargs):
    """Signal để giảm số lượng sản phẩm khi đơn hàng được đánh dấu 'đã giao'"""
    # Chỉ xử lý khi đơn hàng đã tồn tại trong DB (có id)
    if instance.pk:
        try:
            # Lấy đơn hàng cũ từ DB
            old_order = DonHang.objects.get(pk=instance.pk)
            
            # Chỉ xử lý khi trạng thái đổi từ khác "da_giao" sang "da_giao"
            if old_order.trang_thai_don_hang != 'da_giao' and instance.trang_thai_don_hang == 'da_giao':
                giam_so_luong_san_pham(instance)
                        
        except DonHang.DoesNotExist:
            # Đơn hàng mới, không cần xử lý
            pass

