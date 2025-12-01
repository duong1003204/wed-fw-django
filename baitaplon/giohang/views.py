from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse
from sanpham.models import DanhMuc, SanPham
from .models import GioHang, ChiTietGioHang
from django.contrib import messages

@require_POST
def them_vao_gio_hang(request):
    san_pham_id = request.POST.get('san_pham_id')
    
    size = request.POST.get('size')
    color = request.POST.get('color')


    if not san_pham_id or not size or not color:
        messages.error(request, 'Lỗi: Vui lòng chọn đầy đủ Size và Màu sắc.')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    try:
        so_luong = int(request.POST.get('so_luong', 1))
        if so_luong <= 0: 
            so_luong = 1
    except ValueError:
        so_luong = 1

    try:
        san_pham = SanPham.objects.get(id=san_pham_id)
    except SanPham.DoesNotExist:
        messages.error(request, 'Lỗi: Sản phẩm này không tồn tại.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    product_key = f"{san_pham_id}_{size}_{color}"

    if request.user.is_authenticated:
        gio_hang, _ = GioHang.objects.get_or_create(ma_nguoi_dung=request.user)
        
        chi_tiet, created = ChiTietGioHang.objects.get_or_create(
            ma_gio_hang=gio_hang,
            ma_san_pham=san_pham,
            size=size,
            color=color
        )
        
        if not created:
            chi_tiet.so_luong += so_luong # Cộng dồn số lượng
        else:
            chi_tiet.so_luong = so_luong # Tạo mới
        
        chi_tiet.save()

    else:
        gio_hang_session = request.session.get('giohang', {})
        
        if product_key in gio_hang_session:
            gio_hang_session[product_key]['so_luong'] += so_luong
        else:
            # Lưu cả thông tin chi tiết
            gio_hang_session[product_key] = {
                'san_pham_id': san_pham_id,
                'size': size,
                'color': color,
                'so_luong': so_luong
            }

        request.session['giohang'] = gio_hang_session

    messages.success(request, f'Đã thêm "{san_pham.ten_san_pham} ({size}, {color})" vào giỏ hàng.')
    return redirect('giohang:gio_hang_view')

def gio_hang_view(request):
    chi_tiet_gio_hang_list = []
    tong_tien = 0
    shipping_fee = 0  # Phí ship cố định (ví dụ)

    if request.user.is_authenticated:
        # Lấy giỏ hàng từ database
        try:
            gio_hang = GioHang.objects.get(ma_nguoi_dung=request.user)
            # Queryset đã có sẵn mọi thứ
            chi_tiet_gio_hang_list = ChiTietGioHang.objects.filter(ma_gio_hang=gio_hang)
            
            for item in chi_tiet_gio_hang_list:
                # Dùng property @property đã định nghĩa trong models.py
                tong_tien += item.tong_tien_item 
        
        except GioHang.DoesNotExist:
            chi_tiet_gio_hang_list = []

    else:
        # Lấy giỏ hàng từ session (LOGIC ĐÃ THAY ĐỔI)
        gio_hang_session = request.session.get('giohang', {})
        
        # key bây giờ là "1_XL_Red"
        for product_key, item_details in gio_hang_session.items():
            try:
                san_pham_id = item_details['san_pham_id']
                so_luong = item_details['so_luong']
                
                san_pham = SanPham.objects.get(id=int(san_pham_id))
                
                # Sử dụng giá khuyến mãi nếu có và > 0, nếu không thì dùng giá gốc
                if san_pham.giakm and san_pham.giakm > 0:
                    gia_san_pham = san_pham.giakm
                else:
                    gia_san_pham = san_pham.gia
                tong_tien_item = gia_san_pham * so_luong
                tong_tien += tong_tien_item
                
                chi_tiet_gio_hang_list.append({
                    'id_session_key': product_key, # Gửi key này để xóa/cập nhật
                    'ma_san_pham': san_pham,
                    'so_luong': so_luong,
                    'size': item_details['size'],
                    'color': item_details['color'],
                    'tong_tien_item': tong_tien_item,
                })
            except (SanPham.DoesNotExist, ValueError, KeyError):
                continue

    thanh_tien = tong_tien + shipping_fee
    menudanhmuc = DanhMuc.objects.filter(trang_thai=True)

    context = {
        'menudanhmuc': menudanhmuc,
        'chi_tiet_gio_hang': chi_tiet_gio_hang_list,
        'tong_tien': tong_tien, 
        'shipping_fee': shipping_fee,
        'thanh_tien': thanh_tien, 
    }
    return render(request, 'cart.html', context)

@require_http_methods(["POST"])
def quan_ly_gio_hang(request):
    """Xử lý tăng/giảm/xóa sản phẩm trong giỏ hàng - Trả về JSON cho AJAX"""
    item_id = request.POST.get('item_id')
    action = request.POST.get('action') # 'increase', 'decrease', 'remove'

    if not item_id or not action:
        return JsonResponse({'success': False, 'message': 'Yêu cầu không hợp lệ.'}, status=400)

    try:
        if request.user.is_authenticated:
            # Xử lý cho user đã đăng nhập
            chi_tiet = ChiTietGioHang.objects.get(id=item_id, ma_gio_hang__ma_nguoi_dung=request.user)
            
            if action == 'increase':
                chi_tiet.so_luong += 1
                chi_tiet.save()
                so_luong_moi = chi_tiet.so_luong
                tong_tien_item = float(chi_tiet.tong_tien_item)
                message = 'Đã tăng số lượng.'
            
            elif action == 'decrease':
                chi_tiet.so_luong -= 1
                if chi_tiet.so_luong <= 0:
                    chi_tiet.delete()
                    so_luong_moi = 0
                    tong_tien_item = 0
                    message = 'Đã xóa sản phẩm.'
                else:
                    chi_tiet.save()
                    so_luong_moi = chi_tiet.so_luong
                    tong_tien_item = float(chi_tiet.tong_tien_item)
                    message = 'Đã giảm số lượng.'
            
            elif action == 'remove':
                chi_tiet.delete()
                so_luong_moi = 0
                tong_tien_item = 0
                message = 'Đã xóa sản phẩm.'
            else:
                return JsonResponse({'success': False, 'message': 'Hành động không hợp lệ.'}, status=400)
        
        else:
            # Xử lý cho user chưa đăng nhập (session)
            gio_hang_session = request.session.get('giohang', {})
            
            if item_id not in gio_hang_session:
                return JsonResponse({'success': False, 'message': 'Không tìm thấy sản phẩm.'}, status=404)

            if action == 'increase':
                gio_hang_session[item_id]['so_luong'] += 1
                so_luong_moi = gio_hang_session[item_id]['so_luong']
                message = 'Đã tăng số lượng.'
            
            elif action == 'decrease':
                gio_hang_session[item_id]['so_luong'] -= 1
                if gio_hang_session[item_id]['so_luong'] <= 0:
                    del gio_hang_session[item_id]
                    so_luong_moi = 0
                    message = 'Đã xóa sản phẩm.'
                else:
                    so_luong_moi = gio_hang_session[item_id]['so_luong']
                    message = 'Đã giảm số lượng.'
            
            elif action == 'remove':
                del gio_hang_session[item_id]
                so_luong_moi = 0
                message = 'Đã xóa sản phẩm.'
            else:
                return JsonResponse({'success': False, 'message': 'Hành động không hợp lệ.'}, status=400)
            
            request.session['giohang'] = gio_hang_session
            
            # Tính lại tổng tiền cho session
            tong_tien_item = 0
            if so_luong_moi > 0 and item_id in gio_hang_session:
                try:
                    san_pham = SanPham.objects.get(id=int(gio_hang_session[item_id]['san_pham_id']))
                    gia = float(san_pham.giakm) if san_pham.giakm and san_pham.giakm > 0 else float(san_pham.gia)
                    tong_tien_item = gia * so_luong_moi
                except:
                    tong_tien_item = 0

        # Tính lại tổng tiền giỏ hàng
        tong_tien = 0
        if request.user.is_authenticated:
            try:
                gio_hang = GioHang.objects.get(ma_nguoi_dung=request.user)
                chi_tiet_list = ChiTietGioHang.objects.filter(ma_gio_hang=gio_hang)
                for item in chi_tiet_list:
                    tong_tien += float(item.tong_tien_item)
            except:
                tong_tien = 0
        else:
            gio_hang_session = request.session.get('giohang', {})
            for product_key, item_details in gio_hang_session.items():
                try:
                    san_pham = SanPham.objects.get(id=int(item_details['san_pham_id']))
                    gia = float(san_pham.giakm) if san_pham.giakm and san_pham.giakm > 0 else float(san_pham.gia)
                    tong_tien += gia * item_details['so_luong']
                except:
                    continue

        shipping_fee = 0
        thanh_tien = tong_tien + shipping_fee

        return JsonResponse({
            'success': True,
            'message': message,
            'so_luong': so_luong_moi,
            'tong_tien_item': tong_tien_item,
            'tong_tien': tong_tien,
            'thanh_tien': thanh_tien,
            'removed': so_luong_moi == 0
        })

    except ChiTietGioHang.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Không tìm thấy sản phẩm.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Lỗi: {str(e)}'}, status=500)

