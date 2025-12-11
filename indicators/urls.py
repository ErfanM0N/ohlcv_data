from django.urls import path
from indicators import views

app_name = 'indicators'

urlpatterns = [
    path('', views.calculate_indicator, name='calculate_indicator'),
]