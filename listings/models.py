from django.contrib.auth.models import User
from django.db import models
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image

def resize_and_compress_image(image_field, max_width=1200, quality=80):
    """
    On-upload helper to compress, resize, and convert images to WebP format.
    Balances premium visual quality (quality=80) with minimal file size.
    """
    if not image_field:
        return
    try:
        # Reset file pointer before reading to prevent 0-byte uploads
        try:
            image_field.seek(0)
        except Exception:
            pass
            
        img = Image.open(image_field)
        
        # Convert color palette or alpha channels to compatible formats
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            save_mode = 'RGBA'
            format_ext = 'WEBP'
        else:
            img = img.convert('RGB')
            save_mode = 'RGB'
            format_ext = 'WEBP'
            
        # Downscale oversized photos to max_width preserving ratio
        width, height = img.size
        if width > max_width:
            new_height = int((max_width / width) * height)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
        # Buffer image data in memory
        buffer = BytesIO()
        img.save(buffer, format=format_ext, quality=quality, method=4)
        buffer.seek(0)
        
        # Rewrite filename extension to .webp
        original_name = image_field.name
        name_without_ext = original_name.rsplit('.', 1)[0]
        new_filename = f"{name_without_ext}.webp"
        
        image_field.save(new_filename, ContentFile(buffer.read()), save=False)
    except Exception as e:
        print(f"Error compressing uploaded image: {e}")
        # Ensure file pointer is reset to 0 so Django/Cloudinary can still read the original file
        try:
            image_field.seek(0)
        except Exception:
            pass


class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    image = models.ImageField(upload_to='cities/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = "Cities"

    def __str__(self):
        return self.name

class Area(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='areas')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('city', 'slug')
        indexes = [
            models.Index(fields=['city', 'slug']),
        ]

    def __str__(self):
        return f"{self.name} ({self.city.name})"


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
        ('Padvarahalli', 'Padvarahalli'),
        ('Vinayakanagar', 'Vinayakanagar'),
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
    nearby_food_options = models.CharField(max_length=255, blank=True, default='', help_text="List nearby mess, tiffin services, or restaurants")
    description = models.TextField()
    facilities = models.CharField(max_length=200, help_text="Comma separated e.g. WiFi, Food, AC, Parking")
    image = models.ImageField(upload_to='listings/')
    address = models.TextField(default='')
    exact_location = models.CharField(max_length=255, default='', blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    google_place_id = models.CharField(max_length=255, blank=True, default='')
    nearby_landmarks_cache = models.TextField(blank=True, default='')
    phone = models.CharField(max_length=20, default='')
    is_sold = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    whatsapp_clicks_count = models.PositiveIntegerField(default=0)
    
    # Verification fields
    is_verified = models.BooleanField(default=False, help_text="Verified by RoomNest admin")
    verification_status = models.CharField(
        max_length=20, 
        default='Not Requested', 
        choices=(
            ('Not Requested', 'Not Requested'),
            ('Pending', 'Pending'),
            ('Verified', 'Verified'),
            ('Rejected', 'Rejected')
        )
    )
    verification_document = models.FileField(upload_to='verification_docs/', blank=True, null=True)
    verification_notes = models.TextField(blank=True, default='')

    # Custom fields for dynamic categories
    listing_purpose = models.CharField(max_length=20, default='Rent') # Rent, Lease, Sale
    rooms_available = models.IntegerField(default=1) # PG
    sharing_count = models.IntegerField(default=1) # PG (members per room)
    flatmate_preference = models.CharField(max_length=50, blank=True, default='') # Flatmate
    
    GENDER_PREFERENCE_CHOICES = (
        ('Any', 'Any (Boys or Girls)'),
        ('Boys Only', 'Boys Only'),
        ('Girls Only', 'Girls Only'),
    )
    target_gender = models.CharField(max_length=20, choices=GENDER_PREFERENCE_CHOICES, default='Any')
    
    FURNISHING_CHOICES = (
        ('Unfurnished', 'Unfurnished'),
        ('Semi-Furnished', 'Semi-Furnished'),
        ('Fully Furnished', 'Fully Furnished'),
    )
    furnishing = models.CharField(max_length=20, choices=FURNISHING_CHOICES, default='Unfurnished')
    
    commercial_type = models.CharField(max_length=50, blank=True, default='') # Commercial / Office
    built_up_area = models.CharField(max_length=50, blank=True, default='') # Commercial / Office
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='listings')
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='listings')
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=255, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['is_sold', 'created_at']),
            models.Index(fields=['location']),
            models.Index(fields=['price']),
            models.Index(fields=['type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['city', 'slug']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        if self.city and self.slug:
            return reverse('area_page', kwargs={'city_slug': self.city.slug, 'area_slug': self.slug})
        return reverse('details', args=[self.id])

    def get_seo_alt_text(self):
        city_name = self.city.name if self.city else 'Mysore'
        type_lower = self.type.lower()
        if 'pg (men)' in type_lower:
            type_str = f"Boys PG in {city_name}"
        elif 'pg (women)' in type_lower:
            type_str = f"Girls PG in {city_name}"
        elif '1bhk' in type_lower:
            type_str = f"1 BHK Room for Rent in {city_name}"
        elif '2bhk' in type_lower:
            type_str = f"2 BHK Flat in {city_name}"
        elif '3bhk' in type_lower:
            type_str = f"3 BHK Flat in {city_name}"
        elif 'single room' in type_lower:
            type_str = f"Single Room for Rent in {city_name}"
        else:
            type_str = f"{self.type} in {city_name}"
        return f"{'Verified ' if self.is_verified else ''}{type_str}"

    def save(self, *args, **kwargs):
        if self.image and not self.image.name.lower().endswith('.webp'):
            resize_and_compress_image(self.image)

        if not self.slug:
            from django.utils.text import slugify
            type_str = self.type.lower()
            if 'pg' in type_str:
                if 'men' in type_str or self.target_gender == 'Boys Only':
                    type_slug = 'pg-for-boys'
                elif 'women' in type_str or self.target_gender == 'Girls Only':
                    type_slug = 'pg-for-girls'
                else:
                    type_slug = 'pg'
            elif '1bhk' in type_str:
                type_slug = '1-bhk-room'
            elif '2bhk' in type_str:
                type_slug = '2-bhk-flat'
            elif '3bhk' in type_str:
                type_slug = '3-bhk-flat'
            elif 'flatmate' in type_str:
                type_slug = 'flatmate-room'
            elif 'co-living' in type_str:
                type_slug = 'co-living-space'
            else:
                type_slug = slugify(self.type)
                
            purpose_slug = slugify(self.listing_purpose or 'rent')
            area_name = self.area.name if self.area else (self.location or '')
            area_slug = slugify(area_name)
            
            parts = []
            if 'pg' in type_slug:
                parts.append(type_slug)
            else:
                parts.append(type_slug)
                parts.append(f"for-{purpose_slug}")
            if area_slug:
                parts.append(area_slug)
                
            base_slug = '-'.join(parts)
            slug = base_slug
            counter = 1
            
            # Check uniqueness within the same city
            while Listing.objects.filter(city=self.city, slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args, **kwargs)
        
        # Smart cache invalidation (ignores background clicks/view count increases)
        update_fields = kwargs.get('update_fields')
        if update_fields:
            fields_set = {f.name if hasattr(f, 'name') else f for f in update_fields}
            if fields_set.issubset({'views_count', 'whatsapp_clicks_count'}):
                return
        from django.core.cache import cache
        cache.delete(f"listing_detail_{self.id}")

    def delete(self, *args, **kwargs):
        from django.core.cache import cache
        cache.delete(f"listing_detail_{self.id}")
        super().delete(*args, **kwargs)

class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='listings/gallery/')

    def save(self, *args, **kwargs):
        if self.image and not self.image.name.lower().endswith('.webp'):
            resize_and_compress_image(self.image)
        super().save(*args, **kwargs)

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
        indexes = [
            models.Index(fields=['receiver', 'is_read']),
            models.Index(fields=['sender', 'receiver', 'timestamp']),
        ]

class Review(models.Model):
    listing = models.ForeignKey(Listing, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('listing', 'user')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from django.core.cache import cache
        cache.delete(f"listing_detail_{self.listing_id}")

    def delete(self, *args, **kwargs):
        from django.core.cache import cache
        cache.delete(f"listing_detail_{self.listing_id}")
        super().delete(*args, **kwargs)

class Lead(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='leads')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leads_generated', null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    message_content = models.TextField(blank=True, default='')
    lead_type = models.CharField(
        max_length=20, 
        choices=(
            ('WhatsApp', 'WhatsApp Inquiry'), 
            ('Chat', 'Direct Chat Message')
        )
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} - {self.listing.title} ({self.lead_type})"


class PropertySubmission(models.Model):
    PROPERTY_TYPES = (
        ('Room', 'Room'),
        ('PG', 'PG'),
        ('Flat', 'Flat'),
        ('House', 'House'),
        ('Commercial', 'Commercial'),
    )
    
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Under Verification', 'Under Verification'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Published', 'Published'),
    )

    submitter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_submissions')
    submitted_by_name = models.CharField(max_length=100)
    submitted_by_mobile = models.CharField(max_length=20)
    owner_name = models.CharField(max_length=100)
    owner_mobile = models.CharField(max_length=20)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES)
    property_address = models.TextField()
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    photo = models.ImageField(upload_to='submissions/', blank=True, null=True)
    notes = models.TextField(blank=True, default='')
    permission_confirmed = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Referral by {self.submitter.username} - {self.property_type} in {self.city.name if self.city else 'Unknown'}"


class Reward(models.Model):
    TYPE_CHOICES = (
        ('Referral', 'Referral Submission'),
        ('DirectOwner', 'Direct Owner Listing'),
    )
    
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Paid', 'Paid'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rewards')
    reward_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    submission = models.ForeignKey(PropertySubmission, on_delete=models.SET_NULL, null=True, blank=True, related_name='rewards')
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, blank=True, related_name='rewards')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"₹{self.amount} {self.status} for {self.user.username} ({self.reward_type})"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title} (Read: {self.is_read})"


