from django.db import models
from django.utils import timezone

class Poll(models.Model):
    question_text = models.CharField("Anket Sorusu", max_length=255)
    pub_date = models.DateTimeField("Yayınlanma Tarihi", default=timezone.now)
    end_date = models.DateTimeField("Bitiş Tarihi")
    is_active = models.BooleanField("Aktif mi?", default=True)

    class Meta:
        verbose_name = "Anket"
        verbose_name_plural = "Anketler"
        ordering = ['-pub_date']

    def __str__(self):
        return self.question_text

    @property
    def is_expired(self):
        return timezone.now() > self.end_date

class Choice(models.Model):
    poll = models.ForeignKey(Poll, related_name='choices', on_delete=models.CASCADE)
    choice_text = models.CharField("Seçenek", max_length=200)

    class Meta:
        verbose_name = "Seçenek"
        verbose_name_plural = "Seçenekler"

    def __str__(self):
        return f"{self.poll.question_text[:30]}... - {self.choice_text}"

    @property
    def votes_count(self):
        return self.vote_set.count()

class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    username = models.CharField("Oy Veren Vatandaş (Kullanıcı Adı)", max_length=150)
    created_at = models.DateTimeField("Oy Verme Tarihi", auto_now_add=True)

    class Meta:
        verbose_name = "Oy"
        verbose_name_plural = "Oylar"
        unique_together = ('poll', 'username')  # Bir kullanıcı bir ankete sadece bir kez oy verebilir

    def __str__(self):
        return f"{self.username} -> {self.poll.question_text[:20]} ({self.choice.choice_text})"
