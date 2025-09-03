from rest_framework.generics import ListAPIView
from .models import Prediction
from .serializers import PredictionSerializer
from apps.securities.models import Security

class PredictionListView(ListAPIView):
    """
    An API view to list all model predictions for a given security ticker.
    
    Accessed via a URL like: /api/analysis/RELIANCE/predictions/
    """
    serializer_class = PredictionSerializer

    def get_queryset(self):
        """Override to filter predictions based on the ticker in the URL."""
        ticker = self.kwargs['ticker'].upper()
        try:
            security = Security.objects.get(ticker=ticker)
            return Prediction.objects.filter(security=security)
        except Security.DoesNotExist:
            return Prediction.objects.none() # Return an empty queryset if ticker is not found
