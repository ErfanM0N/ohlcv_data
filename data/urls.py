"""
URL configuration for data project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from ohlc.views import get_1d_view, get_4h_view, get_1h_view, get_15m_view
from asset.views import get_symbols_view, get_last_price_view
from trade.views import get_positions_view, place_futures_order_view, get_balance_view, get_trade_history_view



urlpatterns = [
    path('admin/', admin.site.urls),
    path('1d/', get_1d_view, name='get_1d'),
    path('4h/', get_4h_view, name='get_4h'),
    path('1h/', get_1h_view, name='get_1h'),
    path('15m/', get_15m_view, name='get_15m'),
    path('symbols/', get_symbols_view, name='get_symbols'),
    path('positions/', get_positions_view, name='get_positions'),
    path('place_order/', place_futures_order_view, name='place_futures_order'),
    path('balance/', get_balance_view, name='get_balance'),
    path('trade_history/', get_trade_history_view, name='get_trade_history'),  # Assuming this is the correct view for trade history
    path('last_price/', get_last_price_view, name='get_last_price')
]


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)