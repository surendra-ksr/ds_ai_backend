from django.db import models
from core.models import BaseModel
from securities.models import Security

class Prediction(BaseModel):
    MODEL_CHOICES = [
        ('ARIMA', 'ARIMA'),
        ('LSTM', 'LSTM'),
    ]

    security = models.ForeignKey(Security, on_delete=models.CASCADE, related_name='predictions')
    model_name = models.CharField(max_length=10, choices=MODEL_CHOICES)
    prediction_date = models.DateField(help_text="The date for which the prediction is made")
    predicted_value = models.DecimalField(max_digits=12, decimal_places=4)
    prediction_made_at = models.DateTimeField(auto_now_add=True, editable=False, help_text="When the prediction was generated")

    class Meta:
        unique_together = ('security', 'model_name', 'prediction_date')
        ordering = ['-prediction_date']

    def __str__(self):
        return f"{self.model_name} prediction for {self.security.ticker} on {self.prediction_date}"
