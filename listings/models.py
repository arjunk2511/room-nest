from django.contrib.auth.models import User
from django.db import models

class Listing(models.Model):
    TYPE_CHOICES = (
        ('1BHK', '1BHK'),
        ('2BHK', '2BHK'),
        ('3BHK', '3BHK'),
        ('Single Room', 'Single Room'),
        ('PG (Men)', 'PG (Men)'),
        ('PG (Women)', 'PG (Women)'),
        ('Co-living', 'Co-living'),
    )
    
    MYSORE_AREAS = (
        ('Vijayanagar', 'Vijayanagar'),
        ('Gokulam', 'Gokulam'),
        ('Kuvempunagar', 'Kuvempunagar'),
        ('Saraswathipuram', 'Saraswathipuram'),
        ('Jayalakshmipuram', 'Jayalakshmipuram'),
        ('Vontikoppal', 'Vontikoppal'),
        ('Hebbal', 'Hebbal'),
        ('Bannimantap', 'Bannimantap'),
        ('Bogadi', 'Bogadi'),
        ('Siddhartha Layout', 'Siddhartha Layout'),
        ('Other (Mysore)', 'Other (Mysore)'),
    )

    title = models.CharField(max_length=200)
    location = models.CharField(max_length=50, choices=MYSORE_AREAS, default='Vijayanagar')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField()
    facilities = models.CharField(max_length=200, help_text="Comma separated e.g. WiFi, Food, AC, Parking")
    image = models.ImageField(upload_to='listings/')
    address = models.TextField(default='')
    exact_location = models.CharField(max_length=255, default='', blank=True)
    phone = models.CharField(max_length=20, default='')
    is_sold = models.BooleanField(default=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='listings/gallery/')

class Wishlist(models.Model):
    user = models.ForeignKey(User, related_name='wishlist', on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, related_name='wishlisted_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'listing')

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

class Review(models.Model):
    listing = models.ForeignKey(Listing, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('listing', 'user')
