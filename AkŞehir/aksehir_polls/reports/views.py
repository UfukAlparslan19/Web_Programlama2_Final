import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from .models import Report
from .utils import analyze_image_with_google_ai

# ==========================================
# SAYFA GÖRÜNÜMLERİ (TEMPLATE RENDERING)
# ==========================================

@login_required
def dashboard(request):
    """
    Vatandaş Kontrol Paneli.
    Eğer admin ise Belediye Yetkilisi Yönetim Paneline yönlendirilir.
    """
    if request.user.is_staff:
        return redirect('admin_panel')
    return render(request, 'reports/dashboard.html', {'username': request.user.username})

@login_required
def admin_panel(request):
    """
    Belediye Yetkilisi Yönetim Paneli.
    Eğer admin değilse Vatandaş Paneline yönlendirilir.
    """
    if not request.user.is_staff:
        return redirect('dashboard')
    return render(request, 'reports/admin_panel.html', {'username': request.user.username})

@login_required
def report_step1(request):
    """
    1. Adım: Kategori Seçimi
    """
    if request.method == 'POST':
        category = request.POST.get('category')
        if category:
            request.session['report_data'] = {'category': category}
            return redirect('report_step2')
    
    # Yeni bir rapor süreci başlatılıyorsa session'daki eski verileri temizle
    if 'report_data' in request.session:
        del request.session['report_data']
    if 'analysis_result' in request.session:
        del request.session['analysis_result']
        
    return render(request, 'reports/rapor_et_step1.html')

@login_required
def report_step2(request):
    """
    2. Adım: Fotoğraf ve Konum Seçimi
    """
    if 'report_data' not in request.session or 'category' not in request.session['report_data']:
        return redirect('report_step1')
        
    return render(request, 'reports/rapor_et_step2.html', {
        'category': request.session['report_data']['category']
    })

@login_required
def report_process_analysis(request):
    """
    Form post edildiğinde resmi sunucuya kaydeder, Gemini AI analizini başlatır
    ve session'a sonuçları kaydedip 3. adıma yönlendirir.
    """
    if request.method != 'POST':
        return HttpResponse("Geçersiz istek metodu.", status=405)
        
    if 'report_data' not in request.session or 'category' not in request.session['report_data']:
        return redirect('report_step1')
        
    category = request.session['report_data']['category']
    latitude = request.POST.get('latitude')
    longitude = request.POST.get('longitude')
    address = request.POST.get('address', 'Adres belirtilmedi')
    image_file = request.FILES.get('reportImage')
    
    if not all([latitude, longitude, image_file]):
        return HttpResponse("Eksik alanlar: latitude, longitude veya resim yüklenmedi.", status=400)
        
    # Dosya türü kontrolü
    allowed_types = ['image/jpeg', 'image/png', 'image/webp']
    if image_file.content_type not in allowed_types:
        return HttpResponse("Geçersiz dosya türü. Sadece JPG, PNG veya WEBP yükleyebilirsiniz.", status=400)
        
    # Dosyayı kaydet
    fs = FileSystemStorage(location=settings.MEDIA_ROOT)
    # uploads/ klasörünün altına kaydetmek için dosya ismini 'uploads/report_xxx.ext' yapıyoruz
    # Bu db'ye 'uploads/report_xxx.ext' olarak kaydedilmesini ve PHP db yapısıyla uyumlu olmasını sağlar.
    filename = fs.save('uploads/' + image_file.name, image_file)
    image_path = filename # Örn: 'uploads/report_xxx.png'
    
    # Rapor verilerini session'a yaz
    report_data = request.session.get('report_data', {})
    report_data.update({
        'latitude': latitude,
        'longitude': longitude,
        'address': address,
        'image_path': image_path
    })
    request.session['report_data'] = report_data
    
    # Gemini AI Analizi
    full_image_path = fs.path(image_path)
    analysis_result = analyze_image_with_google_ai(full_image_path, category)
    
    # Analiz hatası varsa yüklenen dosyayı silebiliriz veya 'analiz_hatasi' olarak kaydedebiliriz.
    request.session['analysis_result'] = analysis_result
    
    return redirect('report_step3')

@login_required
def report_step3(request):
    """
    3. Adım: Kontrol Et ve Gönder
    """
    if 'report_data' not in request.session or 'analysis_result' not in request.session:
        return redirect('report_step1')
        
    report_data = request.session['report_data']
    analysis_result = request.session['analysis_result']
    
    is_analysis_error = 'error' in analysis_result
    risk_level = analysis_result.get('risk_level', 'Belirsiz')
    ai_description = analysis_result.get('ai_description', 'Analiz açıklaması bulunamadı.')
    
    risk_color_class = 'risk-low'
    if 'orta' in risk_level.lower():
        risk_color_class = 'risk-medium'
    elif 'yüksek' in risk_level.lower():
        risk_color_class = 'risk-high'
        
    return render(request, 'reports/rapor_et_step3.html', {
        'image_path': '/' + report_data['image_path'], # static sunulabilmesi için path'in başına slash koyuyoruz
        'category': report_data['category'],
        'address': report_data['address'],
        'ai_description': ai_description,
        'risk_level': risk_level,
        'risk_color_class': risk_color_class,
        'is_analysis_error': is_analysis_error
    })

@login_required
def report_process_final(request):
    """
    Raporun veritabanına kalıcı olarak kaydedilmesi
    """
    if request.method != 'POST':
        return HttpResponse("Geçersiz istek metodu.", status=405)
        
    if 'report_data' not in request.session or 'analysis_result' not in request.session:
        return redirect('report_step1')
        
    report_data = request.session['report_data']
    analysis_result = request.session['analysis_result']
    
    user_notes = request.POST.get('user_notes', '').strip()
    
    status = 'analiz_hatasi' if 'error' in analysis_result else 'beklemede'
    ai_description = analysis_result.get('ai_description', 'Yapay zeka analizi sırasında bir hata oluştu veya sonuç alınamadı.')
    ai_risk_level = analysis_result.get('risk_level', 'Belirsiz')
    
    try:
        report = Report.objects.create(
            user=request.user,
            category=report_data['category'],
            image=report_data['image_path'],
            latitude=float(report_data['latitude']),
            longitude=float(report_data['longitude']),
            address=report_data['address'],
            ai_description=ai_description,
            ai_risk_level=ai_risk_level,
            user_notes=user_notes,
            status=status
        )
        
        request.session['final_report_result'] = {
            'report_id': report.id,
            'image_path': '/' + report_data['image_path'],
            'category': report_data['category'],
            'address': report_data['address'],
            'ai_description': ai_description,
            'risk_level': ai_risk_level,
            'db_error': None
        }
    except Exception as e:
        request.session['final_report_result'] = {
            'report_id': None,
            'image_path': '/' + report_data['image_path'],
            'category': report_data['category'],
            'address': report_data['address'],
            'ai_description': ai_description,
            'risk_level': ai_risk_level,
            'db_error': f"Veritabanı kayıt hatası: {str(e)}"
        }
        
    # Rapor sürecine ait geçici verileri temizle
    if 'report_data' in request.session:
        del request.session['report_data']
    if 'analysis_result' in request.session:
        del request.session['analysis_result']
        
    return redirect('report_result')

@login_required
def report_result(request):
    """
    Rapor Sonucu sayfası.
    """
    if 'final_report_result' not in request.session:
        return redirect('report_step1')
        
    result_data = request.session['final_report_result']
    is_success = not result_data.get('db_error') and result_data.get('report_id')
    
    risk_level = result_data.get('risk_level', 'Belirsiz')
    risk_color_class = 'risk-low'
    if 'orta' in risk_level.lower():
        risk_color_class = 'risk-medium'
    elif 'yüksek' in risk_level.lower():
        risk_color_class = 'risk-high'
        
    # Sonuç verisini session'dan sil ki sayfa yenilendiğinde tekrar gelmesin
    del request.session['final_report_result']
    
    return render(request, 'reports/rapor_et_result.html', {
        'result_data': result_data,
        'is_success': is_success,
        'risk_color_class': risk_color_class,
        'risk_level': risk_level
    })


# ==========================================
# API ENDPOINT'LERİ (JSON DÖNEN GÖRÜNÜMLER)
# ==========================================

@login_required
def get_reports_api(request):
    """
    Kullanıcının raporlarını listeler. Admin ise sistemdeki tüm raporları getirir.
    """
    if request.user.is_staff:
        # Admin: Tüm raporları getir (ilişkili kullanıcı adıyla birlikte)
        reports = Report.objects.select_related('user').all()
    else:
        # Vatandaş: Sadece kendi raporlarını getir
        reports = Report.objects.filter(user=request.user)
        
    reports_list = []
    for r in reports:
        reports_list.append({
            'id': r.id,
            'category': r.category,
            'image_path': '/' + r.image.name if r.image else '',
            'latitude': r.latitude,
            'longitude': r.longitude,
            'address': r.address,
            'ai_description': r.ai_description,
            'ai_risk_level': r.ai_risk_level,
            'user_notes': r.user_notes,
            'status': r.status,
            'username': r.user.username,
            'created_at': r.created_at.isoformat()
        })
        
    return JsonResponse(reports_list, safe=False)

@login_required
def get_user_stats_api(request):
    """
    Kullanıcının istatistiklerini getirir (Toplam Rapor, Çözülen, Bekleyen, Toplam Puan)
    """
    user_reports = Report.objects.filter(user=request.user)
    
    total_reports = user_reports.count()
    resolved_reports = user_reports.filter(status='çözüldü').count()
    # beklemede veya analiz hatası olanlar bekleyen olarak sayılır
    pending_reports = user_reports.filter(status__in=['beklemede', 'analiz_hatasi']).count()
    
    # 1 resolved report = 100 points
    total_points = resolved_reports * 100
    
    return JsonResponse({
        'total_reports': total_reports,
        'resolved_reports': resolved_reports,
        'pending_reports': pending_reports,
        'total_points': total_points
    })

@csrf_exempt
@login_required
def update_report_status_api(request):
    """
    Adminin rapor durumunu güncellemesini sağlar.
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Bu işlem için yetkiniz yok.'}, status=403)
        
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Yalnızca POST istekleri kabul edilir.'}, status=405)
        
    try:
        data = json.loads(request.body)
        report_id = data.get('report_id')
        new_status = data.get('status')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz JSON formatı.'}, status=400)
        
    if not report_id or not new_status:
        return JsonResponse({'success': False, 'error': 'report_id ve status alanları zorunludur.'}, status=400)
        
    # PHP db yapısındaki Türkçe durum eşleşmeleri
    valid_statuses = ['beklemede', 'onaylandı', 'çözüldü', 'reddedildi', 'analiz_hatasi']
    if new_status not in valid_statuses:
        return JsonResponse({'success': False, 'error': f'Geçersiz durum. Geçerli durumlar: {", ".join(valid_statuses)}'}, status=400)
        
    report = get_object_or_404(Report, pk=report_id)
    report.status = new_status
    report.save()
    
    return JsonResponse({'success': True, 'message': 'Rapor durumu başarıyla güncellendi.'})

@csrf_exempt
@login_required
def delete_report_api(request):
    """
    Vatandaşın kendi raporunu silmesini sağlar.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Yalnızca POST istekleri kabul edilir.'}, status=405)
        
    try:
        data = json.loads(request.body)
        report_id = data.get('report_id')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz JSON formatı.'}, status=400)
        
    if not report_id:
        return JsonResponse({'success': False, 'error': 'report_id zorunludur.'}, status=400)
        
    report = get_object_or_404(Report, pk=report_id)
    
    # Raporun bu kullanıcıya ait olduğundan emin ol (Admin de silebilir)
    if report.user != request.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Bu raporu silmek için yetkiniz yok.'}, status=403)
        
    # Dosyayı sunucudan sil
    if report.image:
        try:
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            fs.delete(report.image.name)
        except Exception:
            pass # Hata olsa bile db kaydını silmeye devam et
            
    report.delete()
    return JsonResponse({'success': True, 'message': 'Rapor başarıyla silindi.'})

def proxy_nominatim_api(request):
    """
    Haritadan seçilen koordinatların adres bilgisini almak için Nominatim reverse proxy.
    PHP'deki proxy_nominatim.php'nin Python karşılığıdır.
    """
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    
    if not lat or not lon:
        return JsonResponse({'error': 'lat ve lon parametreleri gereklidir.'}, status=400)
        
    api_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
    headers = {
        'User-Agent': 'AkSehir_Smart_City_App/1.0 (contact: admin@aksehir.bel.tr)'
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({'error': f'Nominatim API hatası: Durum Kodu {response.status_code}'}, status=502)
    except Exception as e:
        return JsonResponse({'error': f'Adres arama sunucusuyla bağlantı kurulamadı: {str(e)}'}, status=502)
