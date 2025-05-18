from django.http import JsonResponse
from .models import Asset


def get_symbols_view(request):
    coins = list(Asset.objects.filter(enable=True).values_list('symbol', flat=True))
    return JsonResponse({'coins': coins})

