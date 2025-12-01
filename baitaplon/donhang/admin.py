# baitaplon/donhang/admin.py

from django.contrib import admin
from django.urls import path
from .models import DonHang, ChiTietDonHang
from .views import BaoCaoDoanhThuView # Import View báo cáo
from .signals import giam_so_luong_san_pham

class ChiTietDonHangInline(admin.TabularInline):
    model = ChiTietDonHang
    extra = 0
    # Giữ nguyên các trường readonly
    readonly_fields = ['ma_san_pham', 'so_luong', 'gia', 'thanh_tien']

@admin.register(DonHang)
class DonHangAdmin(admin.ModelAdmin):
    # Cấu hình Quản lý Đơn hàng (giữ nguyên logic cũ của bạn)
    list_display = ['id', 'ma_nguoi_dung', 'ngay_dat', 'tong_tien', 'trang_thai_don_hang', 'phuong_thuc_thanh_toan']
    list_filter = ['trang_thai_don_hang', 'ngay_dat', 'phuong_thuc_thanh_toan']
    search_fields = ['ma_nguoi_dung__ho_ten', 'ma_nguoi_dung__username', 'id']
    inlines = [ChiTietDonHangInline]
    readonly_fields = ['ngay_dat', 'tong_tien']
    actions = ['xac_nhan_don', 'danh_dau_da_giao', 'huy_don']
    date_hierarchy = 'ngay_dat'
    list_per_page = 25

    @admin.action(description="✅ Xác nhận đơn hàng")
    def xac_nhan_don(self, request, queryset):
        rows_updated = queryset.update(trang_thai_don_hang='dang_giao')
        self.message_user(request, f"Đã xác nhận {rows_updated} đơn hàng.")

    @admin.action(description="📦 Đánh dấu đã giao")
    def danh_dau_da_giao(self, request, queryset):
        rows_updated = 0
        for order in queryset:
            # Chỉ xử lý nếu chưa phải "da_giao"
            if order.trang_thai_don_hang != 'da_giao':
                # Cập nhật trạng thái
                order.trang_thai_don_hang = 'da_giao'
                order.save()  # Dùng save() để trigger signal (signal sẽ tự động giảm số lượng)
                rows_updated += 1
        
        self.message_user(request, f"Đã đánh dấu {rows_updated} đơn hàng đã giao và giảm số lượng sản phẩm.")

    @admin.action(description="❌ Hủy đơn hàng")
    def huy_don(self, request, queryset):
        rows_updated = queryset.update(trang_thai_don_hang='da_huy')
        self.message_user(request, f"Đã hủy {rows_updated} đơn hàng.")
        
    # --- Bổ sung Logic Báo cáo Doanh thu ---
    
    # 1. Ghi đè get_urls để thêm đường dẫn báo cáo tùy chỉnh
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # Tên URL: admin:donhang_baocao
            path('baocao/', self.admin_site.admin_view(BaoCaoDoanhThuView.as_view()), name='donhang_baocao'),
        ]
        return custom_urls + urls

    # 2. Ghi đè changelist_view để truyền biến 'baocao_url' cho template
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['baocao_url'] = 'baocao/'
        return super().changelist_view(request, extra_context=extra_context)