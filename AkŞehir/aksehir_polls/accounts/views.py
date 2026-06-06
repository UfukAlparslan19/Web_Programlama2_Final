import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

def login_page(request):
    """
    Giriş ve Kayıt sayfasını (eski index.html) render eder.
    Zaten giriş yapmışsa yönlendirir.
    """
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_panel')
        return redirect('dashboard')
    return render(request, 'accounts/login.html')

@csrf_exempt
def login_api(request):
    """
    Fetch/AJAX login isteğini karşılar. Email tabanlı kimlik doğrulama yapar.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Yalnızca POST istekleri kabul edilir.'}, status=405)
        
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz JSON formatı.'}, status=400)
        
    if not email or not password:
        return JsonResponse({'success': False, 'error': 'E-posta ve şifre alanları zorunludur.'}, status=400)
        
    # Email'e karşılık gelen kullanıcıyı bul
    try:
        user_obj = User.objects.get(email=email)
        username = user_obj.username
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Geçersiz e-posta veya şifre.'}, status=401)
        
    # Kimlik doğrula
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        role = 'admin' if user.is_staff else 'vatandas'
        return JsonResponse({
            'success': True,
            'message': 'Giriş başarılı.',
            'user': {
                'id': user.id,
                'username': user.username,
                'role': role
            }
        })
    else:
        return JsonResponse({'success': False, 'error': 'Geçersiz e-posta veya şifre.'}, status=401)

@csrf_exempt
def register_api(request):
    """
    Fetch/AJAX kayıt isteğini karşılar.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Yalnızca POST istekleri kabul edilir.'}, status=405)
        
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz JSON formatı.'}, status=400)
        
    if not username or not email or not password:
        return JsonResponse({'success': False, 'message': 'Kullanıcı adı, e-posta ve şifre zorunludur.'}, status=400)
        
    if len(password) < 8:
        return JsonResponse({'success': False, 'message': 'Şifre en az 8 karakter olmalıdır.'}, status=400)
        
    # Çakışma kontrolü
    if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
        return JsonResponse({'success': False, 'message': 'Bu kullanıcı adı veya e-posta zaten kullanılıyor.'}, status=409)
        
    try:
        # Yeni kullanıcı oluştur
        user = User.objects.create_user(username=username, email=email, password=password)
        # default vatandaş rolü (is_staff=False, Django'da default'tur)
        user.save()
        return JsonResponse({'success': True, 'message': 'Kullanıcı başarıyla oluşturuldu.'}, status=201)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Kullanıcı oluşturulurken hata: {str(e)}'}, status=500)

@csrf_exempt
def logout_view(request):
    """
    Oturumu kapatır ve login sayfasına yönlendirir.
    Hem POST hem GET destekler (PHP'deki çıkış bağlantısı ve API'si ile uyumluluk için).
    """
    logout(request)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.method == 'POST':
        return JsonResponse({'success': True})
    return redirect('login_page')

def session_status_api(request):
    """
    PHP session_status.php eşdeğeri. Giriş yapan kullanıcının bilgilerini döner.
    """
    if request.user.is_authenticated:
        role = 'admin' if request.user.is_staff else 'vatandas'
        return JsonResponse({
            'loggedin': True,
            'id': request.user.id,
            'username': request.user.username,
            'role': role
        })
    return JsonResponse({'loggedin': False})
