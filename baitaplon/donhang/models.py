from django.db import models
from nguoidung.models import NguoiDung
from sanpham.models import SanPham

class DonHang(models.Model):
    TRANG_THAI_CHOICES = [
        ('cho_xu_ly', 'Chờ xử lý'),
        ('dang_giao', 'Đang giao hàng'),
        ('da_giao', 'Đã giao'),
        ('da_huy', 'Đã hủy'),
    ]

    ma_nguoi_dung = models.ForeignKey(NguoiDung, on_delete=models.CASCADE)
    ngay_dat = models.DateTimeField(auto_now_add=True)
    
    # SỬA LỖI: Thêm default=0
    tong_tien = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    
    # SỬA LỖI: Thêm default rỗng
    dia_chi_giao = models.CharField(max_length=255, default='') 
    
    phuong_thuc_thanh_toan = models.CharField(max_length=50, default='') # Thêm default
    trang_thai_don_hang = models.CharField(max_length=20, choices=TRANG_THAI_CHOICES, default='cho_xu_ly')
    ghi_chu = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Đơn hàng #{self.id} - {self.ma_nguoi_dung.ho_ten}"
    
    def get_trang_thai_display_name(self):
        """Trả về tên hiển thị của trạng thái đơn hàng"""
        return dict(self.TRANG_THAI_CHOICES).get(self.trang_thai_don_hang, self.trang_thai_don_hang)

class ChiTietDonHang(models.Model):
    ma_don_hang = models.ForeignKey(DonHang, on_delete=models.CASCADE, related_name="chi_tiet")
    ma_san_pham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    so_luong = models.IntegerField(default=1) # Thêm default
    
    # Thêm size và color để biết giảm biến thể nào
    size = models.CharField(max_length=50, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    
    # SỬA LỖI: Thêm default=0
    gia = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # SỬA LỖI: Thêm default=0
    thanh_tien = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.ma_san_pham.ten_san_pham} ({self.so_luong})"