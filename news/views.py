from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timezone as dt_timezone
from .models import NewsArticle
from .serializers import NewsArticleSerializer


@api_view(['GET'])
def get_articles_by_timerange(request):
    """
    Get news articles within a time range
    
    Query Parameters:
        - start_time (required): Unix timestamp for start time
        - end_time (optional): Unix timestamp for end time. If not provided, uses current time
    
    Example:
        /api/articles/?start_time=1704067200&end_time=1704153600
    """
    
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    
    if not start_time:
        return Response(
            {'error': 'start_time parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        start_time = int(start_time)
        start_datetime = datetime.fromtimestamp(start_time, tz=dt_timezone.utc)
    except (ValueError, OSError):
        return Response(
            {'error': 'Invalid start_time. Must be a valid Unix timestamp'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if end_time:
        try:
            end_time = int(end_time)
            end_datetime = datetime.fromtimestamp(end_time, tz=dt_timezone.utc)
        except (ValueError, OSError):
            return Response(
                {'error': 'Invalid end_time. Must be a valid Unix timestamp'},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        end_datetime = timezone.now()
    
    if start_datetime > end_datetime:
        return Response(
            {'error': 'start_time must be before end_time'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    articles = NewsArticle.objects.filter(
        published_on__gte=start_datetime,
        published_on__lte=end_datetime
    ).order_by('-published_on')
    
    total_count = NewsArticle.objects.filter(
        published_on__gte=start_datetime,
        published_on__lte=end_datetime
    ).count()
    
    serializer = NewsArticleSerializer(articles, many=True)
    
    return Response({
        'success': True,
        'data': serializer.data,
        'meta': {
            'total_count': total_count,
            'returned_count': len(serializer.data),
            'start_time': start_datetime.isoformat(),
            'end_time': end_datetime.isoformat()
        }
    })