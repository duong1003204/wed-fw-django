from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib import messages

from donhang.models import DonHang, ChiTietDonHang 
from .models import NguoiDung 
from giohang.models import GioHang, ChiTietGioHang
from sanpham.models import DanhMuc, SanPham 
from django.db import transaction
from .forms import NguoiDungCreationForm 

def profile(request):
    menudanhmuc = DanhMuc.objects.filter(trang_thai=True)
    return render(request, 'profile.html', {'menudanhmuc': menudanhmuc})

def chuyen_gio_hang_session_vao_db(request):
    menudanhmuc = DanhMuc.objects.filter(trang_thai=True)

    if 'giohang' not in request.session or not request.user.is_authenticated:
        return
    gio_hang_db, created = GioHang.objects.get_or_create(ma_nguoi_dung=request.user) 
    gio_hang_session = request.session.get('giohang')
    if not gio_hang_session:
        return
    try:
        with transaction.atomic():
            for product_key, item_details in gio_hang_session.items():
                try:
                    san_pham_id = int(item_details['san_pham_id'])
                    so_luong_session = int(item_details['so_luong'])
                    size_session = item_details['size']
                    color_session = item_details['color']
                    san_pham = SanPham.objects.get(id=san_pham_id)
                    chi_tiet, created = ChiTietGioHang.objects.get_or_create(
                        ma_gio_hang=gio_hang_db,
                        ma_san_pham=san_pham,
                        size=size_session,
                        color=color_session
                    )
                    if created:
                        chi_tiet.so_luong = so_luong_session
                    else:
                        chi_tiet.so_luong += so_luong_session
                    chi_tiet.save()
                except (SanPham.DoesNotExist, ValueError, KeyError):
                    continue
        del request.session['giohang']
    except Exception as e:
        print(f"Lỗi khi chuyển giỏ hàng session: {e}")


def dangnhap_view(request):
    if request.user.is_authenticated:
        return redirect('trangchu:index')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.trang_thai:  # Kiểm tra trạng thái tài khoản
                    auth_login(request, user)
                    chuyen_gio_hang_session_vao_db(request) 
                    messages.success(request, f"Chào mừng trở lại, {user.ho_ten or username}!")
                    next_url = request.GET.get('next', '/')
                    return redirect(next_url)
                else:
                    messages.error(request, "Tài khoản của bạn đã bị khóa.")
            else:
                messages.error(request, "Tên đăng nhập hoặc mật khẩu không đúng.")
        else:
            messages.error(request, "Tên đăng nhập hoặc mật khẩu không đúng.")
    else:
        form = AuthenticationForm()
    menudanhmuc = DanhMuc.objects.filter(trang_thai=True)

    return render(request, 'login.html', {'form': form, 'menudanhmuc': menudanhmuc})

def dangky_view(request):
    if request.user.is_authenticated:
        return redirect('trangchu:index') 
    if request.method == 'POST':
        form = NguoiDungCreationForm(request.POST) 
        if form.is_valid():
            user = form.save() 
            GioHang.objects.get_or_create(ma_nguoi_dung=user) 
            auth_login(request, user)
            chuyen_gio_hang_session_vao_db(request)
            messages.success(request, f"Đăng ký thành công! Chào mừng {user.ho_ten or user.username}!") 
            return redirect('trangchu:index')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}", extra_tags='danger') 
            return render(request, 'register.html', {'form': form})
    else:
        form = NguoiDungCreationForm() 
    menudanhmuc = DanhMuc.objects.filter(trang_thai=True)

    return render(request, 'register.html', {'form': form, 'menudanhmuc': menudanhmuc})

def dangxuat_view(request):
    auth_logout(request)
    messages.info(request, "Bạn đã đăng xuất.")
    return redirect('/')

@login_required
def profile_view(request):

    user = request.user
    password_form = PasswordChangeForm(user)
  
    active_tab = 'profile' 

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            active_tab = 'profile' # Đặt tab active
            ho_ten = request.POST.get('ho_ten')
            so_dien_thoai = request.POST.get('so_dien_thoai')
            dia_chi = request.POST.get('dia_chi')
            
            user.ho_ten = ho_ten
            user.so_dien_thoai = so_dien_thoai
            user.dia_chi = dia_chi
            user.save()
            
            messages.success(request, 'Cập nhật thông tin cá nhân thành công!')
            return redirect('nguoidung:profile')

        elif action == 'change_password':
            active_tab = 'password' 
            password_form = PasswordChangeForm(user, request.POST)
            
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user) 
                messages.success(request, 'Đổi mật khẩu thành công!')
                return redirect('nguoidung:profile') # Redirect về trang profile (tab mặc định)
            else:
                messages.error(request, 'Đổi mật khẩu thất bại. Vui lòng kiểm tra các lỗi bên dưới.')
    
    orders = DonHang.objects.filter(ma_nguoi_dung=user).order_by('-ngay_dat')
    menudanhmuc = DanhMuc.objects.filter(trang_thai=True)
    
    context = {
        'menudanhmuc': menudanhmuc,
        'orders': orders,
        'password_form': password_form, # Gửi form (có lỗi hoặc rỗng)
        'active_tab': active_tab      # Gửi tab đang active
    }
    return render(request, 'profile.html', context)


@login_required
@require_POST 
def cancel_order_view(request, order_id):
    order = get_object_or_404(DonHang, id=order_id, ma_nguoi_dung=request.user)
    if order.trang_thai_don_hang == 'cho_xu_ly':
        order.trang_thai_don_hang = 'da_huy' 
        order.save()
        messages.success(request, f'Đã hủy thành công đơn hàng #{order.id}.')
    else:
        # Lấy tên trạng thái từ choices (DonHang đã được import ở đầu file)
        trang_thai_dict = dict(DonHang.TRANG_THAI_CHOICES)
        trang_thai_display = trang_thai_dict.get(order.trang_thai_don_hang, order.trang_thai_don_hang)
        messages.error(request, f'Không thể hủy đơn hàng #{order.id} (Trạng thái: {trang_thai_display}).')
    return redirect('nguoidung:profile') 


@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(DonHang, id=order_id, ma_nguoi_dung=request.user)
    order_items = order.chi_tiet.all() 
    context = {
        'order': order,
        'order_items': order_items
    }
    return render(request, 'order_detail.html', context)