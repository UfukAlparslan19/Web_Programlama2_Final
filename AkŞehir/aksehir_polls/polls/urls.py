from django.urls import path
from . import views

urlpatterns = [
    path('polls/', views.get_polls, name='get_polls'),
    path('polls/<int:poll_id>/vote/', views.cast_vote, name='cast_vote'),
    path('polls/all/', views.get_all_polls_api, name='get_all_polls'),
    path('polls/create/', views.create_poll_api, name='create_poll'),
    path('polls/<int:poll_id>/delete/', views.delete_poll_api, name='delete_poll'),
]
