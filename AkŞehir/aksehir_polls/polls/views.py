import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Poll, Choice, Vote

def get_polls(request):
    """
    Aktif ve yayında olan anketleri listeler.
    Kullanıcı adı parametre olarak gönderilirse kullanıcının oy durumu bilgisini de ekler.
    """
    username = request.GET.get('username', '').strip()
    
    # Sadece aktif ve yayınlanma tarihi gelmiş anketleri getir
    polls = Poll.objects.filter(is_active=True, pub_date__lte=timezone.now())
    
    polls_data = []
    for poll in polls:
        choices_data = []
        total_votes = 0
        
        # Seçenekleri ve oylarını hesapla
        for choice in poll.choices.all():
            v_count = choice.votes_count
            total_votes += v_count
            choices_data.append({
                'id': choice.id,
                'choice_text': choice.choice_text,
                'votes_count': v_count
            })
            
        # Kullanıcının bu ankete oy verip vermediğini kontrol et
        user_voted = False
        user_choice_id = None
        
        if username:
            try:
                user_vote = Vote.objects.get(poll=poll, username=username)
                user_voted = True
                user_choice_id = user_vote.choice.id
            except Vote.DoesNotExist:
                user_voted = False
                
        polls_data.append({
            'id': poll.id,
            'question_text': poll.question_text,
            'pub_date': poll.pub_date.isoformat(),
            'end_date': poll.end_date.isoformat(),
            'is_expired': poll.is_expired,
            'total_votes': total_votes,
            'choices': choices_data,
            'user_voted': user_voted,
            'user_choice_id': user_choice_id
        })
        
    return JsonResponse({'success': True, 'polls': polls_data}, safe=False)

@csrf_exempt
def cast_vote(request, poll_id):
    """
    Belirli bir ankete oy verilmesini sağlar.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Yalnızca POST istekleri kabul edilir.'}, status=405)
        
    poll = get_object_or_404(Poll, pk=poll_id)
    
    # Anketin geçerliliğini kontrol et
    if not poll.is_active:
        return JsonResponse({'success': False, 'error': 'Bu anket aktif değildir.'}, status=400)
        
    if poll.is_expired:
        return JsonResponse({'success': False, 'error': 'Bu anketin süresi dolmuştur.'}, status=400)
        
    try:
        data = json.loads(request.body)
        choice_id = data.get('choice_id')
        username = data.get('username', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz JSON formatı.'}, status=400)
        
    if not choice_id or not username:
        return JsonResponse({'success': False, 'error': 'Seçenek ve kullanıcı adı zorunludur.'}, status=400)
        
    # Seçeneğin bu ankete ait olup olmadığını kontrol et
    try:
        choice = poll.choices.get(pk=choice_id)
    except Choice.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Seçenek bu ankete ait değil veya bulunamadı.'}, status=400)
        
    # Kullanıcının zaten oy verip vermediğini kontrol et
    if Vote.objects.filter(poll=poll, username=username).exists():
        return JsonResponse({'success': False, 'error': 'Bu ankette zaten oy kullandınız.'}, status=400)
        
    # Oyu kaydet
    Vote.objects.create(poll=poll, choice=choice, username=username)
    
    # Güncel anket sonuçlarını hesapla ve dön
    choices_data = []
    total_votes = 0
    for c in poll.choices.all():
        v_count = c.votes_count
        total_votes += v_count
        choices_data.append({
            'id': c.id,
            'choice_text': c.choice_text,
            'votes_count': v_count
        })
        
    return JsonResponse({
        'success': True, 
        'message': 'Oy başarıyla kaydedildi.',
        'poll_results': {
            'poll_id': poll.id,
            'total_votes': total_votes,
            'choices': choices_data,
            'user_voted': True,
            'user_choice_id': choice.id
        }
    })

@csrf_exempt
def get_all_polls_api(request):
    """
    Admin için aktif/pasif tüm anketleri listeler.
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Bu işlem için yetkiniz yok.'}, status=403)
        
    polls = Poll.objects.all().order_by('-pub_date')
    polls_data = []
    
    for poll in polls:
        choices_data = []
        total_votes = 0
        for choice in poll.choices.all():
            v_count = choice.votes_count
            total_votes += v_count
            choices_data.append({
                'id': choice.id,
                'choice_text': choice.choice_text,
                'votes_count': v_count
            })
            
        polls_data.append({
            'id': poll.id,
            'question_text': poll.question_text,
            'pub_date': poll.pub_date.isoformat(),
            'end_date': poll.end_date.isoformat(),
            'is_active': poll.is_active,
            'is_expired': poll.is_expired,
            'total_votes': total_votes,
            'choices': choices_data
        })
        
    return JsonResponse({'success': True, 'polls': polls_data})

@csrf_exempt
def create_poll_api(request):
    """
    Adminin yeni anket oluşturmasını sağlar.
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Bu işlem için yetkiniz yok.'}, status=403)
        
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Yalnızca POST istekleri kabul edilir.'}, status=405)
        
    try:
        data = json.loads(request.body)
        question_text = data.get('question_text', '').strip()
        end_date_str = data.get('end_date') # Örn: '2026-06-30'
        choices = data.get('choices', [])
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz JSON formatı.'}, status=400)
        
    if not question_text or not end_date_str or not choices:
        return JsonResponse({'success': False, 'error': 'question_text, end_date ve en az bir choice zorunludur.'}, status=400)
        
    if len(choices) < 2:
        return JsonResponse({'success': False, 'error': 'En az 2 seçenek eklemelisiniz.'}, status=400)
        
    try:
        # Tarih formatını ayrıştır (örn: YYYY-MM-DD veya YYYY-MM-DDTHH:MM)
        from django.utils.dateparse import parse_datetime
        from django.utils.timezone import make_aware
        import datetime
        
        # Eğer tarih sadece gün formatındaysa saat bilgisini günün sonuna ayarla
        if len(end_date_str) == 10:
            end_date_str += "T23:59:59"
            
        end_date = parse_datetime(end_date_str)
        if not end_date:
            # Fallback to date parsing
            parsed_date = datetime.datetime.strptime(end_date_str[:10], "%Y-%m-%d")
            end_date = make_aware(datetime.datetime.combine(parsed_date.date(), datetime.time(23, 59, 59)))
        else:
            if timezone.is_naive(end_date):
                end_date = make_aware(end_date)
                
        # Anketi oluştur
        poll = Poll.objects.create(
            question_text=question_text,
            pub_date=timezone.now(),
            end_date=end_date,
            is_active=True
        )
        
        # Seçenekleri oluştur
        for choice_text in choices:
            choice_text = choice_text.strip()
            if choice_text:
                Choice.objects.create(poll=poll, choice_text=choice_text)
                
        return JsonResponse({'success': True, 'message': 'Anket başarıyla oluşturuldu.'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Anket oluşturulurken hata: {str(e)}'}, status=500)

@csrf_exempt
def delete_poll_api(request, poll_id):
    """
    Adminin anketi silmesini sağlar.
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Bu işlem için yetkiniz yok.'}, status=403)
        
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Yalnızca POST istekleri kabul edilir.'}, status=405)
        
    poll = get_object_or_404(Poll, pk=poll_id)
    poll.delete()
    
    return JsonResponse({'success': True, 'message': 'Anket başarıyla silindi.'})

