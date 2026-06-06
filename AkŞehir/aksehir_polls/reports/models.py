from django.db import models
from django.contrib.auth.models import User

class Report(models.Model):
    STATUS_CHOICES = [
        ('beklemede', 'Beklemede'),
        ('onaylandı', 'Onaylandı'),
        ('çözüldü', 'Çözüldü'),
        ('reddedildi', 'Reddedildi'),
        ('analiz_hatasi', 'Analiz Hatası'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Raporlayan Vatandaş")
    category = models.CharField("Kategori", max_length=100)
    image = models.ImageField("Rapor Görseli", upload_to='uploads/')
    latitude = models.FloatField("Enlem")
    longitude = models.FloatField("Boylam")
    address = models.TextField("Adres", default="Adres belirtilmedi")
    ai_description = models.TextField("Yapay Zeka Açıklaması", blank=True, null=True)
    ai_risk_level = models.CharField("Yapay Zeka Risk Seviyesi", max_length=50, blank=True, null=True)
    user_notes = models.TextField("Kullanıcı Ek Notu", blank=True, null=True)
    status = models.CharField("Durum", max_length=30, choices=STATUS_CHOICES, default='beklemede')
    created_at = models.DateTimeField("Oluşturulma Tarihi", auto_now_add=True)

    class Meta:
        verbose_name = "Rapor"
        verbose_name_plural = "Raporlar"
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.id} - {self.user.username} - {self.category} ({self.status})"
