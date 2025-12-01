from django.contrib import admin
from .models import GioHang, ChiTietGioHang


@admin.register(GioHang)
class GioHangAdmin(admin.ModelAdmin):
    list_display = ('id', 'ma_nguoi_dung', 'ngay_tao', 'ngay_cap_nhat')
    list_filter = ('ngay_tao',)
    search_fields = ('ma_nguoi_dung__username', 'ma_nguoi_dung__ho_ten')
    readonly_fields = ('ngay_tao', 'ngay_cap_nhat')
    date_hierarchy = 'ngay_tao'


@admin.register(ChiTietGioHang)
class ChiTietGioHangAdmin(admin.ModelAdmin):
    list_display = ('id', 'ma_gio_hang', 'ma_san_pham', 'size', 'color', 'so_luong', 'ngay_them')
    list_filter = ('ngay_them', 'size', 'color')
    search_fields = ('ma_san_pham__ten_san_pham', 'ma_gio_hang__ma_nguoi_dung__username')
    readonly_fields = ('ngay_them',)
    date_hierarchy = 'ngay_them'


