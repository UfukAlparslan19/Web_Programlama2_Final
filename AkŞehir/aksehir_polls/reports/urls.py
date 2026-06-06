from django.urls import path
from . import views

urlpatterns = [
    # Şablon Sayfaları (PHP isimleriyle uyumlu rotalar)
    path('dashboard.php', views.dashboard, name='dashboard'),
    path('admin.php', views.admin_panel, name='admin_panel'),
    path('rapor-et.php', views.report_step1, name='report_step1'),
    path('rapor-et-adim-2.php', views.report_step2, name='report_step2'),
    path('rapor-et-islem-analiz.php', views.report_process_analysis, name='report_process_analysis'),
    path('rapor-et-adim-3.php', views.report_step3, name='report_step3'),
    path('rapor-et-islem-son.php', views.report_process_final, name='report_process_final'),
    path('rapor-et-sonuc.php', views.report_result, name='report_result'),
    
    # API Rotaları (PHP API yollarıyla tam uyumlu)
    path('api/get_reports.php', views.get_reports_api, name='get_reports_api'),
    path('api/get_user_stats.php', views.get_user_stats_api, name='get_user_stats_api'),
    path('api/update_report_status.php', views.update_report_status_api, name='update_report_status_api'),
    path('api/delete_report.php', views.delete_report_api, name='delete_report_api'),
    path('api/proxy_nominatim.php', views.proxy_nominatim_api, name='proxy_nominatim_api'),
]
