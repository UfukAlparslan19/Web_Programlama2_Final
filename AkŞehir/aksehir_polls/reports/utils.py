import base64
import requests
import json
import mimetypes

GOOGLE_AI_API_KEY = 'AIzaSyD0bG1aiiYk_KxtgTC21CxVWP7WEvNhDJQ'

def analyze_image_with_google_ai(image_path, category):
    """
    Verilen resmi ve kategoriyi Gemini API ile analiz eder.
    PHP'deki analyzeImageWithGoogleAI fonksiyonunun Python karşılığıdır.
    """
    try:
        api_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GOOGLE_AI_API_KEY}'
        
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/jpeg"
            
        prompt = f"""Sen, bir akıllı şehir projesi olan 'AkŞehir' için çevre sorunlarını analiz eden uzman bir yapay zeka asistanısın. Görevin, kullanıcı tarafından gönderilen fotoğrafları inceleyerek, sorunu tespit etmek, risk seviyesini belirlemek ve çözüm için bir öneri sunmaktır.

Kullanıcı bu raporu '{category}' kategorisinde gönderdi.

Lütfen ekteki fotoğrafı analiz et ve cevabını SADECE ve SADECE RFC 8259 uyumlu bir JSON objesi formatında döndür. JSON objesi dışında hiçbir metin, açıklama veya "```json" gibi işaretler kullanma.

JSON objesi şu alanları içermelidir:
1.  `risk_seviyesi`: Sorunun aciliyetini ve çevresel etkisini belirten bir dize. Olası değerler: "Düşük Risk", "Orta Risk", "Yüksek Risk".
2.  `olay_tespiti`: Fotoğrafta ne gördüğünü nesnel bir şekilde, kısa ve net (en fazla 15 kelime) bir cümleyle özetleyen bir dize. Örnek: 'Sokak kenarına yığılmış evsel atıklar ve çöp poşetleri.'
3.  `oneri`: Bu sorunun çözümü için belediye birimlerine yönelik kısa ve uygulanabilir bir eylem önerisi (en fazla 20 kelime). Örnek: 'Mobil temizlik ekibinin bölgeye yönlendirilerek atıkları toplaması ve bölgeye bir uyarı levhası koyması.'"""

        data = {
            'contents': [
                {
                    'parts': [
                        {'text': prompt},
                        {
                            'inline_data': {
                                'mime_type': mime_type,
                                'data': image_data
                            }
                        }
                    ]
                }
            ]
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(api_url, headers=headers, json=data, timeout=45)
        
        if response.status_code != 200:
            return {'error': f'API isteği başarısız oldu. Durum Kodu: {response.status_code}'}
            
        response_data = response.json()
        
        try:
            ai_response_text = response_data['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return {'error': 'Yapay zeka analizinden geçerli bir yanıt alınamadı.'}
            
        # JSON temizleme
        cleaned_text = ai_response_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        cleaned_text = cleaned_text.strip()
        
        analysis_json = json.loads(cleaned_text)
        
        if 'risk_seviyesi' not in analysis_json or 'olay_tespiti' not in analysis_json or 'oneri' not in analysis_json:
            return {'error': 'Yapay zeka analizinden eksik alanlar döndü.'}
            
        return {
            'risk_level': analysis_json['risk_seviyesi'],
            'ai_description': f"Tespit: {analysis_json['olay_tespiti']} | Öneri: {analysis_json['oneri']}"
        }
        
    except Exception as e:
        return {'error': f'Analiz hatası: {str(e)}'}
