from django.db import models

# Create your models here.
class DanhMuc(models.Model):
    ten_danh_muc = models.CharField(max_length=100)
    mo_ta = models.TextField(blank=True, null=True)
    trang_thai = models.BooleanField(default=True)
    
    def __str__(self):
        return self.ten_danh_muc
    
class SanPham(models.Model):
    ma_danh_muc = models.ForeignKey(DanhMuc, on_delete=models.CASCADE)
    ten_san_pham = models.CharField(max_length=200)
    mo_ta = models.TextField(blank=True, null=True)
    gia = models.DecimalField(max_digits=10, decimal_places=2)
    giakm = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=None)
    anh_dai_dien = models.ImageField(upload_to='sanpham/', blank=True, null=True)
    trang_thai = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.ten_san_pham} - {self.ma_danh_muc.ten_danh_muc}"
    
    @property
    def gia_hien_tai(self):
        """Trả về giá hiện tại (ưu tiên giá khuyến mãi nếu có)"""
        if self.giakm and self.giakm > 0:
            return self.giakm
        return self.gia
    
    @property
    def co_khuyen_mai(self):
        """Kiểm tra xem sản phẩm có đang khuyến mãi không"""
        return self.giakm and self.giakm > 0 and self.giakm < self.gia
    
class BienTheSanPham(models.Model):
    ma_san_pham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    kich_thuoc = models.CharField(max_length=50, blank=True, null=True)
    mau_sac = models.CharField(max_length=50, blank=True, null=True)
    so_luong = models.PositiveIntegerField(default=0)
    hinh_anh = models.ImageField(upload_to='sanpham/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.ma_san_pham.ten_san_pham} - {self.kich_thuoc} - {self.mau_sac} (SL: {self.so_luong})"
    

