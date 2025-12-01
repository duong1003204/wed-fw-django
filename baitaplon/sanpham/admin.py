from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from .models import DanhMuc, SanPham, BienTheSanPham


# ==========================
# FORM: Biến thể sản phẩm
# ==========================
class BienTheForm(forms.ModelForm):
    class Meta:
        model = BienTheSanPham
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        kich_thuoc = cleaned_data.get('kich_thuoc')
        mau_sac = cleaned_data.get('mau_sac')
        so_luong = cleaned_data.get('so_luong')
        hinh_anh = cleaned_data.get('hinh_anh')

        if not kich_thuoc:
            raise ValidationError("⚠️ Vui lòng nhập kích thước cho biến thể.")
        if not mau_sac:
            raise ValidationError("⚠️ Vui lòng nhập màu sắc cho biến thể.")
        if so_luong is None or so_luong <= 0:
            raise ValidationError("⚠️ Số lượng phải lớn hơn 0.")
        if not hinh_anh:
            raise ValidationError("⚠️ Bạn phải thêm ảnh cho biến thể.")

        return cleaned_data


# ==========================
# INLINE: Biến thể sản phẩm
# ==========================
class BienTheInline(admin.TabularInline):
    model = BienTheSanPham
    form = BienTheForm
    extra = 1
    fields = ('kich_thuoc', 'mau_sac', 'so_luong', 'hinh_anh', 'xem_anh')
    readonly_fields = ('xem_anh',)

    def xem_anh(self, obj):
        if obj.hinh_anh:
            return format_html('<img src="{}" width="60" height="60" style="object-fit:cover;border-radius:8px;" />', obj.hinh_anh.url)
        return "Không có ảnh"
    xem_anh.short_description = "Xem ảnh"


# ==========================
# FORM: Sản phẩm
# ==========================
class SanPhamForm(forms.ModelForm):
    class Meta:
        model = SanPham
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        ten_san_pham = cleaned_data.get('ten_san_pham')
        ma_danh_muc = cleaned_data.get('ma_danh_muc')
        gia = cleaned_data.get('gia')
        anh_dai_dien = cleaned_data.get('anh_dai_dien')

        if not ten_san_pham:
            raise ValidationError("⚠️ Bạn phải nhập tên sản phẩm.")
        if not ma_danh_muc:
            raise ValidationError("⚠️ Bạn phải chọn danh mục.")
        if gia is None or gia <= 0:
            raise ValidationError("⚠️ Giá sản phẩm phải lớn hơn 0.")
        if not anh_dai_dien:
            raise ValidationError("⚠️ Bạn phải thêm ảnh đại diện cho sản phẩm.")

        return cleaned_data


# ==========================
# ADMIN: Sản phẩm
# ==========================
@admin.register(SanPham)
class SanPhamAdmin(admin.ModelAdmin):
    form = SanPhamForm
    list_display = ('ten_san_pham', 'ma_danh_muc', 'gia', 'giakm', 'trang_thai', 'xem_anh')
    search_fields = ('ten_san_pham', 'mo_ta')
    list_filter = ('ma_danh_muc', 'trang_thai')
    readonly_fields = ('xem_anh',)
    inlines = [BienTheInline]
    list_per_page = 25

    def xem_anh(self, obj):
        if obj.anh_dai_dien:
            return format_html('<img src="{}" width="70" height="70" style="object-fit:cover;border-radius:8px;" />', obj.anh_dai_dien.url)
        return "Không có ảnh"
    xem_anh.short_description = "Ảnh đại diện"


# ==========================
# ADMIN: Danh mục
# ==========================
@admin.register(DanhMuc)
class DanhMucAdmin(admin.ModelAdmin):
    list_display = ('ten_danh_muc', 'trang_thai')
    search_fields = ('ten_danh_muc',)
