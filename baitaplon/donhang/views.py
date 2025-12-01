from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.views import View
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta
import hmac
import hashlib
import urllib.parse
import json
import pytz
from openpyxl import Workbook

# Import các models
from giohang.models import GioHang, ChiTietGioHang
from .models import DonHang, ChiTietDonHang

# --- CẤU HÌNH VNPAY DEMO ---
VNPAY_TMNCODE = "BTQM0MAO" 
VNPAY_HASH_SECRET_KEY = "4TYACLKZ3JHF73VO5QCLQXZXJS9WMTZM" 
VNPAY_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html" 
VNPAY_RETURN_URL = 'http://127.0.0.1:8000/donhang/vnpay_return/' 


# --- 1. VIEW HIỂN THỊ TRANG CHECKOUT ---
def checkout_view(request):
    # === FIX: KIỂM TRA ĐĂNG NHẬP THỦ CÔNG ===
    if not request.user.is_authenticated:
        messages.warning(request, "Vui lòng đăng nhập để tiến hành thanh toán.")
        # Sửa 'login' thành 'dang_nhap' để khớp với urls.py của bạn
        return redirect('nguoidung:dang_nhap') 
    # =========================================

    # Lấy giỏ hàng của người dùng
    try:
        gio_hang_db = GioHang.objects.get(ma_nguoi_dung=request.user)
        cart_items = ChiTietGioHang.objects.filter(ma_gio_hang=gio_hang_db)
        
        if not cart_items.exists():
            messages.error(request, "Giỏ hàng của bạn đang trống.")
            return redirect('giohang:gio_hang_view')
            
    except GioHang.DoesNotExist:
        messages.error(request, "Giỏ hàng của bạn đang trống.")
        return redirect('giohang:gio_hang_view')

    # Tính toán tổng tiền
    subtotal = 0
    for item in cart_items:
        subtotal += item.tong_tien_item 
    
    shipping_fee = 10 
    total = subtotal + shipping_fee

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'total': total,
        'user': request.user 
    }
    return render(request, 'checkout.html', context)


# --- 2. VIEW XỬ LÝ ĐẶT HÀNG (COD & VNPAY) ---
@login_required
def place_order_view(request):
    if request.method == 'POST':
        # Lấy thông tin từ form
        ho_ten = request.POST.get('ho_ten', '').strip()
        email = request.POST.get('email', '').strip()
        so_dien_thoai = request.POST.get('so_dien_thoai', '').strip()
        dia_chi = request.POST.get('dia_chi_giao', '').strip()
        payment_method = request.POST.get('payment_method', 'cod')
        ghi_chu = request.POST.get('ghi_chu', '').strip()
        
        # Validation
        if not ho_ten:
            messages.error(request, "Vui lòng nhập họ tên.")
            return redirect('donhang:checkout')
        if not dia_chi:
            messages.error(request, "Vui lòng nhập địa chỉ giao hàng.")
            return redirect('donhang:checkout')
        if payment_method not in ['cod', 'vnpay']:
            messages.error(request, "Phương thức thanh toán không hợp lệ.")
            return redirect('donhang:checkout') 

        try:
            gio_hang_db = GioHang.objects.get(ma_nguoi_dung=request.user)
            cart_items = ChiTietGioHang.objects.filter(ma_gio_hang=gio_hang_db)
            if not cart_items.exists():
                messages.error(request, "Giỏ hàng trống, không thể đặt hàng.")
                return redirect('giohang:gio_hang_view')
        except GioHang.DoesNotExist:
            messages.error(request, "Lỗi giỏ hàng.")
            return redirect('giohang:gio_hang_view')

        subtotal = 0
        for item in cart_items:
            subtotal += item.tong_tien_item
        shipping_fee = 10
        total = subtotal + shipping_fee
        
        # --- Tạo Đơn Hàng ---
        try:
            don_hang = DonHang.objects.create(
                ma_nguoi_dung=request.user,
                tong_tien=total,
                dia_chi_giao=dia_chi,
                phuong_thuc_thanh_toan=payment_method,
                trang_thai_don_hang='cho_xu_ly', 
                ghi_chu=ghi_chu
            )

            # Chuyển sản phẩm từ giỏ hàng sang Chi Tiết Đơn Hàng
            for item in cart_items:
                # Sử dụng giá khuyến mãi nếu có, nếu không thì dùng giá gốc
                gia_ban = item.ma_san_pham.giakm if item.ma_san_pham.giakm and item.ma_san_pham.giakm > 0 else item.ma_san_pham.gia
                
                # Tạo chi tiết đơn hàng với size và color (nếu migration đã chạy)
                try:
                    ChiTietDonHang.objects.create(
                        ma_don_hang=don_hang,
                        ma_san_pham=item.ma_san_pham,
                        so_luong=item.so_luong,
                        size=item.size,  # Lưu size
                        color=item.color,  # Lưu color
                        gia=gia_ban,
                        thanh_tien=item.tong_tien_item 
                    )
                except Exception as e:
                    # Nếu chưa có field size/color (chưa chạy migration), tạo không có size/color
                    ChiTietDonHang.objects.create(
                        ma_don_hang=don_hang,
                        ma_san_pham=item.ma_san_pham,
                        so_luong=item.so_luong,
                        gia=gia_ban,
                        thanh_tien=item.tong_tien_item 
                    )
            
            # Xóa giỏ hàng (ChiTietGioHang)
            cart_items.delete()

            # --- Xử lý phương thức thanh toán ---
            if payment_method == 'cod':
                # (Thanh toán khi nhận hàng)
                messages.success(request, 'Đặt hàng COD thành công!')
                return redirect('donhang:order_success', order_id=don_hang.id)

            elif payment_method == 'vnpay':
                # (Thanh toán VNPAY)
                
                # Cài đặt múi giờ Việt Nam
                vnp_CreateDate = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y%m%d%H%M%S')
                vnp_Amount = int(total * 100) 
                vnp_OrderInfo = f"Thanh toan don hang {don_hang.id}"
                vnp_TxnRef = str(don_hang.id) 
                vnp_IpAddr = request.META.get('REMOTE_ADDR')

                input_data = {
                    "vnp_Version": "2.1.0",
                    "vnp_Command": "pay",
                    "vnp_TmnCode": VNPAY_TMNCODE,
                    "vnp_Amount": vnp_Amount,
                    "vnp_CreateDate": vnp_CreateDate,
                    "vnp_CurrCode": "VND",
                    "vnp_IpAddr": vnp_IpAddr,
                    "vnp_Locale": "vn",
                    "vnp_OrderInfo": vnp_OrderInfo,
                    "vnp_OrderType": "other",
                    "vnp_ReturnUrl": VNPAY_RETURN_URL,
                    "vnp_TxnRef": vnp_TxnRef,
                }
                
                # Sắp xếp data
                input_data = dict(sorted(input_data.items()))
                
                # Tạo query string
                query_string = urllib.parse.urlencode(input_data, safe="%")
                
                # Tạo hash
                hash_data = VNPAY_HASH_SECRET_KEY + "&" + query_string
                secure_hash = hmac.new(
                    VNPAY_HASH_SECRET_KEY.encode(), 
                    query_string.encode(), 
                    hashlib.sha512
                ).hexdigest()
                
                # URL thanh toán cuối cùng
                payment_url = VNPAY_URL + "?" + query_string + "&vnp_SecureHash=" + secure_hash
                
                return HttpResponseRedirect(payment_url)

        except Exception as e:
            messages.error(request, f"Đã xảy ra lỗi khi tạo đơn hàng: {e}")
            return redirect('donhang:checkout')

    messages.error(request, "Yêu cầu không hợp lệ.")
    return redirect('donhang:checkout')


# --- 3. VIEW XỬ LÝ KẾT QUẢ VNPAY TRẢ VỀ ---
@login_required
def vnpay_return_view(request):
    # Lấy dữ liệu VNPAY trả về
    input_data = request.GET.dict()
    
    if input_data:
        vnp_SecureHash = input_data.pop('vnp_SecureHash', '')
        
        # Sắp xếp lại dữ liệu
        input_data = dict(sorted(input_data.items()))
        
        # Tạo query string
        query_string = urllib.parse.urlencode(input_data, safe="%")
        
        # Tạo hash mới
        hash_data = VNPAY_HASH_SECRET_KEY + "&" + query_string
        new_secure_hash = hmac.new(
            VNPAY_HASH_SECRET_KEY.encode(), 
            query_string.encode(), 
            hashlib.sha512
        ).hexdigest()
        
        # Lấy mã đơn hàng
        order_id = input_data.get('vnp_TxnRef', None)
        try:
            don_hang = DonHang.objects.get(id=order_id, ma_nguoi_dung=request.user)
        except DonHang.DoesNotExist:
            messages.error(request, "Lỗi: Không tìm thấy đơn hàng.")
            return redirect('trangchu:index') 

        # --- KIỂM TRA HASH (Quan trọng) ---
        if new_secure_hash == vnp_SecureHash:
            vnp_ResponseCode = input_data.get('vnp_ResponseCode', None)
            
            # --- THANH TOÁN THÀNH CÔNG ---
            if vnp_ResponseCode == '00':
                messages.success(request, f"Thanh toán VNPAY thành công cho đơn hàng #{order_id}!")
                return redirect('donhang:order_success', order_id=don_hang.id)
            
            # --- THANH TOÁN THẤT BẠI (hoặc bị hủy) ---
            else:
                # Cập nhật trạng thái đơn hàng là đã hủy
                don_hang.trang_thai_don_hang = 'da_huy'
                don_hang.save()
                
                error_messages = {
                    '07': 'Trừ tiền thành công. Giao dịch bị nghi ngờ (liên quan tới lừa đảo, giao dịch bất thường).',
                    '09': 'Thẻ/Tài khoản chưa đăng ký dịch vụ InternetBanking',
                    '10': 'Xác thực giao dịch không thành công do: Nhập sai mật khẩu quá số lần quy định.',
                    '11': 'Đã hết hạn chờ thanh toán. Xin vui lòng thực hiện lại giao dịch.',
                    '12': 'Thẻ/Tài khoản bị khóa.',
                    '51': 'Tài khoản không đủ số dư để thực hiện giao dịch.',
                    '65': 'Tài khoản đã vượt quá hạn mức giao dịch trong ngày.',
                    '75': 'Ngân hàng thanh toán đang bảo trì.',
                    '79': 'Nhập sai mật khẩu thanh toán quá số lần quy định.',
                }
                error_msg = error_messages.get(vnp_ResponseCode, f'Mã lỗi: {vnp_ResponseCode}')
                messages.error(request, f"Thanh toán VNPAY thất bại ({error_msg}). Đơn hàng #{order_id} đã bị hủy.")
                return redirect('giohang:gio_hang_view') 
        
        # --- LỖI SAI HASH ---
        else:
            messages.error(request, "Lỗi bảo mật: Chữ ký VNPAY không hợp lệ.")
            don_hang.trang_thai_don_hang = 'da_huy' 
            don_hang.save()
            return redirect('giohang:gio_hang_view')
            
    messages.error(request, "Không nhận được dữ liệu trả về từ VNPAY.")
    return redirect('giohang:gio_hang_view')


# --- 4. VIEW ĐẶT HÀNG THÀNH CÔNG ---
@login_required
def order_success_view(request, order_id):
    try:
        order = DonHang.objects.get(id=order_id, ma_nguoi_dung=request.user)
        order_items = order.chi_tiet.all()
    except DonHang.DoesNotExist:
        messages.error(request, "Không tìm thấy đơn hàng.")
        return redirect('trangchu:index')
        
    context = {
        'order': order,
        'order_items': order_items
    }
    return render(request, 'order_success.html', context)


@method_decorator(staff_member_required, name='dispatch')
class BaoCaoDoanhThuView(View):
    template_name = 'admin/donhang/baocao_doanhthu.html'

    def get(self, request):

        # ========= XỬ LÝ EXPORT EXCEL =========
        if request.GET.get("export") == "excel":
            return self.export_excel(request)

        # ========= MẶC ĐỊNH 30 NGÀY =========
        ngay_ket_thuc = timezone.now().date()
        ngay_bat_dau = ngay_ket_thuc - timedelta(days=30)

        group_by = request.GET.get('group_by', 'day')

        start_date_param = request.GET.get('start_date')
        end_date_param = request.GET.get('end_date')
        selected_month_year = request.GET.get('month_year')

        # ======= Xử lý lọc thời gian =======
        if group_by == 'month' and selected_month_year:
            dt = datetime.strptime(selected_month_year, "%Y-%m").date()
            ngay_bat_dau = dt.replace(day=1)

            next_month = ngay_bat_dau.replace(day=28) + timedelta(days=4)
            ngay_ket_thuc = (next_month - timedelta(days=next_month.day)).date()

        elif start_date_param and end_date_param:
            ngay_bat_dau = datetime.strptime(start_date_param, "%Y-%m-%d").date()
            ngay_ket_thuc = datetime.strptime(end_date_param, "%Y-%m-%d").date()

        # ======= Lọc đơn hàng theo thời gian =======
        don_hang_da_giao = DonHang.objects.filter(
            trang_thai_don_hang='da_giao',
            ngay_dat__date__gte=ngay_bat_dau,
            ngay_dat__date__lte=ngay_ket_thuc
        ).order_by('-ngay_dat')

        # ======= Doanh thu theo thời gian =======

        truncate_by = TruncDay('ngay_dat')
        date_format = '%Y-%m-%d'

        doanh_thu_theo_thoi_gian = don_hang_da_giao.annotate(
            group_date=truncate_by
        ).values('group_date').annotate(
            tong_doanh_thu=Sum('tong_tien')
        ).order_by('group_date')

        # ======= Tổng quan theo bộ lọc =======
        tong_quan = don_hang_da_giao.aggregate(
            tong_doanh_thu=Sum('tong_tien'),
            tong_don_hang=Count('id')
        )

        # ======= ⭐ TOP SẢN PHẨM MỌI THỜI GIAN =======
        top_query = ChiTietDonHang.objects.all().values(
            'ma_san_pham__ten_san_pham'
        ).annotate(
            tong_so_luong_ban=Sum('so_luong'),
            tong_doanh_thu_san_pham=Sum('thanh_tien')
        )

        top_san_pham = top_query.order_by('-tong_so_luong_ban')[:10]
        bottom_san_pham = top_query.order_by('tong_so_luong_ban')[:10]

        # ======= Tổng doanh thu toàn hệ thống =======
        tong_doanh_thu_all = DonHang.objects.filter(
            trang_thai_don_hang='da_giao'
        ).aggregate(
            total=Sum('tong_tien')
        )['total'] or 0

        context = {
            'title': 'Báo cáo Doanh thu & Sản phẩm',

            # dữ liệu lọc
            'don_hang_list': don_hang_da_giao,
            'doanh_thu_theo_thoi_gian': doanh_thu_theo_thoi_gian,
            'tong_quan': tong_quan,

            # dữ liệu mọi thời gian
            'top_san_pham': top_san_pham,
            'bottom_san_pham': bottom_san_pham,
            'tong_doanh_thu_all': tong_doanh_thu_all,

            # filter binding
            'ngay_bat_dau': ngay_bat_dau,
            'ngay_ket_thuc': ngay_ket_thuc,
            'selected_month_year': selected_month_year,
            'group_by': group_by,
            'date_format': date_format,
        }

        return render(request, self.template_name, context)

    # =============== EXPORT EXCEL ===============
    def export_excel(self, request):
        wb = Workbook()
        ws = wb.active
        ws.title = "BaoCaoDoanhThu"

        ws.append(["Mã đơn", "Khách hàng", "Ngày đặt", "Tổng tiền"])

        orders = DonHang.objects.filter(trang_thai_don_hang='da_giao')

        for o in orders:
            ws.append([
                o.id,
                o.ma_nguoi_dung.username if o.ma_nguoi_dung else "",
                o.ngay_dat.strftime("%d/%m/%Y %H:%M"),
                o.tong_tien,
            ])

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response['Content-Disposition'] = 'attachment; filename="baocao_doanhthu.xlsx"'

        wb.save(response)
        return response