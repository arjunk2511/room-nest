from django.db import models
from django.contrib.auth.models import User

class Subscription(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.CharField(max_length=20, default='Pending', choices=STATUS_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.payment_status} ({'Active' if self.is_active else 'Inactive'})"
