from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from .models import DanhMuc, SanPham, BienTheSanPham
from django.db.models import Q
from django.core.paginator import Paginator

# --- Các view chitietsanpham, colors_for_size, image_for_variant giữ nguyên ---
def chitietsanpham(request, id):
    ctsp = get_object_or_404(SanPham, id=id, trang_thai=True)
    sizes = list(ctsp.bienthesanpham_set.values_list('kich_thuoc', flat=True).distinct())
    colors = list(ctsp.bienthesanpham_set.values_list('mau_sac', flat=True).distinct())
    menudanhmuc = DanhMuc.objects.filter(trang_thai=True)
    sanpham = SanPham.objects.filter(trang_thai=True).exclude(id=id).order_by('?')[:4]

    return render(request, 'detail.html', {'ctsp': ctsp, 'sizes': sizes, 'colors': colors, 'menudanhmuc': menudanhmuc, 'sanpham': sanpham})

def colors_for_size(request):
    size = request.GET.get('size')
    sp_id = request.GET.get('sp_id')
    
    if not size or not sp_id:
        return JsonResponse({'colors': []}, status=400)
    
    try:
        bien_the = BienTheSanPham.objects.filter(ma_san_pham_id=sp_id, kich_thuoc=size)
        colors = list(bien_the.values_list('mau_sac', flat=True).distinct())
        return JsonResponse({'colors': colors})
    except Exception as e:
        return JsonResponse({'colors': [], 'error': str(e)}, status=500)


def image_for_variant(request):
    size = request.GET.get('size')
    color = request.GET.get('color')
    sp_id = request.GET.get('sp_id')
    
    if not size or not color or not sp_id:
        return JsonResponse({'img_url': ''}, status=400)
    
    try:
        bt = BienTheSanPham.objects.filter(ma_san_pham_id=sp_id, kich_thuoc=size, mau_sac=color).first()
        if bt and bt.hinh_anh:
            img_url = bt.hinh_anh.url
        else:
            # Nếu không có ảnh biến thể, lấy ảnh đại diện của sản phẩm
            try:
                sp = SanPham.objects.get(id=sp_id)
                img_url = sp.anh_dai_dien.url if sp.anh_dai_dien else ''
            except SanPham.DoesNotExist:
                img_url = ''
        return JsonResponse({'img_url': img_url})
    except Exception as e:
        return JsonResponse({'img_url': '', 'error': str(e)}, status=500)

# --- CẬP NHẬT VIEW SHOP ---
def shop(request):
    menudanhmuc = DanhMuc.objects.filter(trang_thai=True)
    sanpham_list = SanPham.objects.filter(trang_thai=True).order_by('id')

    # BỔ SUNG: Lấy tất cả màu và size để hiển thị bộ lọc
    # Lấy các giá trị không rỗng và sắp xếp
    all_colors = BienTheSanPham.objects.exclude(mau_sac__isnull=True).exclude(mau_sac__exact='').values_list('mau_sac', flat=True).distinct().order_by('mau_sac')
    all_sizes = BienTheSanPham.objects.exclude(kich_thuoc__isnull=True).exclude(kich_thuoc__exact='').values_list('kich_thuoc', flat=True).distinct().order_by('kich_thuoc')

    query = request.GET.get('timkiem')
    if query:
        sanpham_list = sanpham_list.filter(
            Q(ten_san_pham__icontains=query) | Q(mo_ta__icontains=query)
        )

    # --- LOGIC LỌC NÂNG CAO (Giữ nguyên từ trước) ---
    selected_prices = request.GET.getlist('price')
    selected_colors = request.GET.getlist('color')
    selected_sizes = request.GET.getlist('size')

    if selected_prices:
        price_query = Q()
        # Filter: nếu có giakm và giakm > 0 thì check giakm, nếu không thì check gia
        if "0-100" in selected_prices: 
            price_query.add(
                (Q(giakm__isnull=False) & Q(giakm__gt=0) & Q(giakm__gte=0) & Q(giakm__lte=100)) |
                ((Q(giakm__isnull=True) | Q(giakm__lte=0)) & Q(gia__gte=0) & Q(gia__lte=100)),
                Q.OR
            )
        if "100-200" in selected_prices: 
            price_query.add(
                (Q(giakm__isnull=False) & Q(giakm__gt=0) & Q(giakm__gte=100) & Q(giakm__lte=200)) |
                ((Q(giakm__isnull=True) | Q(giakm__lte=0)) & Q(gia__gte=100) & Q(gia__lte=200)),
                Q.OR
            )
        if "200-300" in selected_prices: 
            price_query.add(
                (Q(giakm__isnull=False) & Q(giakm__gt=0) & Q(giakm__gte=200) & Q(giakm__lte=300)) |
                ((Q(giakm__isnull=True) | Q(giakm__lte=0)) & Q(gia__gte=200) & Q(gia__lte=300)),
                Q.OR
            )
        if "300-400" in selected_prices: 
            price_query.add(
                (Q(giakm__isnull=False) & Q(giakm__gt=0) & Q(giakm__gte=300) & Q(giakm__lte=400)) |
                ((Q(giakm__isnull=True) | Q(giakm__lte=0)) & Q(gia__gte=300) & Q(gia__lte=400)),
                Q.OR
            )
        if "400-500" in selected_prices: 
            price_query.add(
                (Q(giakm__isnull=False) & Q(giakm__gt=0) & Q(giakm__gte=400) & Q(giakm__lte=500)) |
                ((Q(giakm__isnull=True) | Q(giakm__lte=0)) & Q(gia__gte=400) & Q(gia__lte=500)),
                Q.OR
            )
        
        if price_query:
            sanpham_list = sanpham_list.filter(price_query)

    if selected_colors:
        sanpham_list = sanpham_list.filter(bienthesanpham__mau_sac__in=selected_colors).distinct()

    if selected_sizes:
        sanpham_list = sanpham_list.filter(bienthesanpham__kich_thuoc__in=selected_sizes).distinct()
    # --- KẾT THÚC LOGIC LỌC ---

    paginator = Paginator(sanpham_list, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'shop.html', {
        'menudanhmuc': menudanhmuc,
        'sanpham': page_obj,
        'query': query,
        
        'all_colors': all_colors, # <-- Gửi data động
        'all_sizes': all_sizes,   # <-- Gửi data động
        
        'selected_prices': selected_prices,
        'selected_colors': selected_colors,
        'selected_sizes': selected_sizes,
    })

# --- CẬP NHẬT VIEW SHOP_DANHMUC ---
def shop_danhmuc(request, id):
    menudanhmuc = DanhMuc.objects.filter(trang_thai=True)
    danhmuc = get_object_or_404(DanhMuc, id=id)
    sanpham_list = SanPham.objects.filter(ma_danh_muc_id=id, trang_thai=True).order_by('id')

    # BỔ SUNG: Lấy tất cả màu và size để hiển thị bộ lọc
    all_colors = BienTheSanPham.objects.exclude(mau_sac__isnull=True).exclude(mau_sac__exact='').values_list('mau_sac', flat=True).distinct().order_by('mau_sac')
    all_sizes = BienTheSanPham.objects.exclude(kich_thuoc__isnull=True).exclude(kich_thuoc__exact='').values_list('kich_thuoc', flat=True).distinct().order_by('kich_thuoc')

    # --- LOGIC LỌC NÂNG CAO (Giữ nguyên từ trước) ---
    selected_prices = request.GET.getlist('price')
    selected_colors = request.GET.getlist('color')
    selected_sizes = request.GET.getlist('size')

    if selected_prices:
        price_query = Q()
        # Filter: nếu có giakm và giakm > 0 thì check giakm, nếu không thì check gia
        if "0-100" in selected_prices: 
            price_query.add(
                (Q(giakm__isnull=False) & Q(giakm__gt=0) & Q(giakm__gte=0) & Q(giakm__lte=100)) |
                ((Q(giakm__isnull=True) | Q(giakm__lte=0)) & Q(gia__gte=0) & Q(gia__lte=100)),
                Q.OR
            )
        if "100-200" in selected_prices: 
            price_query.add(
                (Q(giakm__isnull=False) & Q(giakm__gt=0) & Q(giakm__gte=100) & Q(giakm__lte=200)) |
                ((Q(giakm__isnull=True) | Q(giakm__lte=0)) & Q(gia__gte=100) & Q(gia__lte=200)),
                Q.OR
            )
        if "200-300" in selected_prices: 
            price_query.add(
                (Q(giakm__isnull=False) & Q(giakm__gt=0) & Q(giakm__gte=200) & Q(giakm__lte=300)) |
                ((Q(giakm__isnull=True) | Q(giakm__lte=0)) & Q(gia__gte=200) & Q(gia__lte=300)),
                Q.OR
            )
        if "300-400" in selected_prices: 
            price_query.add(
                (Q(giakm__isnull=False) & Q(giakm__gt=0) & Q(giakm__gte=300) & Q(giakm__lte=400)) |
                ((Q(giakm__isnull=True) | Q(giakm__lte=0)) & Q(gia__gte=300) & Q(gia__lte=400)),
                Q.OR
            )
        if "400-500" in selected_prices: 
            price_query.add(
                (Q(giakm__isnull=False) & Q(giakm__gt=0) & Q(giakm__gte=400) & Q(giakm__lte=500)) |
                ((Q(giakm__isnull=True) | Q(giakm__lte=0)) & Q(gia__gte=400) & Q(gia__lte=500)),
                Q.OR
            )
        
        if price_query:
            sanpham_list = sanpham_list.filter(price_query)

    if selected_colors:
        sanpham_list = sanpham_list.filter(bienthesanpham__mau_sac__in=selected_colors).distinct()

    if selected_sizes:
        sanpham_list = sanpham_list.filter(bienthesanpham__kich_thuoc__in=selected_sizes).distinct()
    # --- KẾT THÚC LOGIC LỌC ---

    paginator = Paginator(sanpham_list, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'shop.html', {
        'menudanhmuc': menudanhmuc, 
        'danhmuc': danhmuc, 
        'sanpham': page_obj,
        
        'all_colors': all_colors, # <-- Gửi data động
        'all_sizes': all_sizes,   # <-- Gửi data động

        'selected_prices': selected_prices,
        'selected_colors': selected_colors,
        'selected_sizes': selected_sizes,
    })

# --- VIEW AJAX ĐỂ FILTER KHÔNG RELOAD TRANG ---
def shop_filter_ajax(request):
    """View AJAX để filter sản phẩm không reload trang"""
    sanpham_list = SanPham.objects.filter(trang_thai=True).order_by('id')
    
    # Lấy query search nếu có
    query = request.GET.get('timkiem')
    if query:
        sanpham_list = sanpham_list.filter(
            Q(ten_san_pham__icontains=query) | Q(mo_ta__icontains=query)
        )
    
    # Lấy các filter
    selected_prices = request.GET.getlist('price')
    selected_colors = request.GET.getlist('color')
    selected_sizes = request.GET.getlist('size')
    
    # Áp dụng filter giá - đơn giản: filter theo giá hiện tại (giakm nếu có, không thì gia)
    if selected_prices:
        price_conditions = Q()
        
        for price_range in selected_prices:
            min_price, max_price = map(int, price_range.split('-'))
            
            # Filter: nếu có giakm và giakm > 0 thì dùng giakm, nếu không thì dùng gia
            # Cách đơn giản: check cả giakm và gia, nếu một trong hai nằm trong khoảng thì hiển thị
            condition = (
                Q(giakm__isnull=False, giakm__gt=0, giakm__gte=min_price, giakm__lte=max_price) |
                Q(gia__gte=min_price, gia__lte=max_price)
            )
            price_conditions.add(condition, Q.OR)
        
        if price_conditions:
            sanpham_list = sanpham_list.filter(price_conditions)
    
    # Áp dụng filter màu
    if selected_colors:
        sanpham_list = sanpham_list.filter(bienthesanpham__mau_sac__in=selected_colors).distinct()
    
    # Áp dụng filter size
    if selected_sizes:
        sanpham_list = sanpham_list.filter(bienthesanpham__kich_thuoc__in=selected_sizes).distinct()
    
    # Phân trang
    paginator = Paginator(sanpham_list, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Render HTML của danh sách sản phẩm
    products_html = render_to_string('shop_products.html', {
        'sanpham': page_obj,
        'query': query,
        'selected_prices': selected_prices,
        'selected_colors': selected_colors,
        'selected_sizes': selected_sizes,
    }, request=request)
    
    return JsonResponse({
        'success': True,
        'html': products_html,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
    })