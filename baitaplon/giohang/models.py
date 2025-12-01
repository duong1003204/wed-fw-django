from django.db import models
from nguoidung.models import NguoiDung
from sanpham.models import SanPham

class GioHang(models.Model):
    ma_nguoi_dung = models.ForeignKey(NguoiDung, on_delete=models.CASCADE)
    ngay_tao = models.DateTimeField(auto_now_add=True)
    ngay_cap_nhat = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Giỏ hàng {self.ma_nguoi_dung.ho_ten}"


class ChiTietGioHang(models.Model):
    ma_gio_hang = models.ForeignKey(GioHang, on_delete=models.CASCADE)
    ma_san_pham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    

    size = models.CharField(max_length=50, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    
    so_luong = models.IntegerField(default=1)
    ngay_them = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Hiển thị rõ hơn trong admin
        return f"{self.ma_san_pham.ten_san_pham} ({self.size}, {self.color}) - {self.so_luong}"

    # Thêm property để tính tổng tiền (giống logic view)
    # Giúp template cart.html gọi .tong_tien_item dễ dàng
    @property
    def tong_tien_item(self):
        # Sử dụng giá khuyến mãi nếu có và > 0, nếu không thì dùng giá gốc
        if self.ma_san_pham.giakm and self.ma_san_pham.giakm > 0:
            gia = self.ma_san_pham.giakm
        else:
            gia = self.ma_san_pham.gia
        return gia * self.so_luong