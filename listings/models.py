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
        ('Flatmate', 'Flatmate'),
        ('Commercial Space', 'Commercial Space'),
        ('Office Space', 'Office Space'),
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
    deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    available_from = models.CharField(max_length=100, default='Immediately')
    
    # House Rules
    FOOD_CHOICES = (('Any', 'Any'), ('Veg Only', 'Veg Only'), ('Non-Veg Allowed', 'Non-Veg Allowed'))
    food_preference = models.CharField(max_length=20, choices=FOOD_CHOICES, default='Any')
    
    CURFEW_CHOICES = (('No Curfew', 'No Curfew'), ('9 PM', '9 PM'), ('10 PM', '10 PM'), ('11 PM', '11 PM'), ('Strict', 'Strict'))
    curfew = models.CharField(max_length=20, choices=CURFEW_CHOICES, default='No Curfew')
    
    VISITORS_CHOICES = (('Allowed', 'Allowed'), ('Not Allowed', 'Not Allowed'), ('Daytime Only', 'Daytime Only'))
    visitors = models.CharField(max_length=20, choices=VISITORS_CHOICES, default='Allowed')
    
    landmark = models.CharField(max_length=200, blank=True, default='', help_text="e.g. 5 mins from JSS College")
    description = models.TextField()
    facilities = models.CharField(max_length=200, help_text="Comma separated e.g. WiFi, Food, AC, Parking")
    image = models.ImageField(upload_to='listings/')
    address = models.TextField(default='')
    exact_location = models.CharField(max_length=255, default='', blank=True)
    phone = models.CharField(max_length=20, default='')
    is_sold = models.BooleanField(default=False)

    
    # Custom fields for dynamic categories
    listing_purpose = models.CharField(max_length=20, default='Rent') # Rent, Lease, Sale
    rooms_available = models.IntegerField(default=1) # PG
    sharing_count = models.IntegerField(default=1) # PG (members per room)
    flatmate_preference = models.CharField(max_length=50, blank=True, default='') # Flatmate
    commercial_type = models.CharField(max_length=50, blank=True, default='') # Commercial / Office
    built_up_area = models.CharField(max_length=50, blank=True, default='') # Commercial / Office
    
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
