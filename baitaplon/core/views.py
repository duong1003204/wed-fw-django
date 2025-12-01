# core/views.py
from django.http import JsonResponse
from django.db.models import Q
from sanpham.models import SanPham

def search_suggestions(request):
    q = request.GET.get('q', '').strip()
    results = []
    
    if len(q) >= 2:
        try:
            qs = SanPham.objects.filter(
                Q(ten_san_pham__icontains=q) |
                Q(mo_ta__icontains=q),
                trang_thai=True
            ).distinct()[:10]

            results = [{
                'id': p.id,
                'name': p.ten_san_pham,
                'price': float(p.giakm if p.giakm and p.giakm > 0 else p.gia),
                'image': p.anh_dai_dien.url if p.anh_dai_dien else '/static/img/no-image.png',
                'url': f"/sanpham/chitietsanpham/{p.id}/"
            } for p in qs]
        except Exception as e:
            # Log error in production, return empty results
            return JsonResponse({'results': [], 'error': 'Có lỗi xảy ra'}, status=500)

    return JsonResponse({'results': results})