from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True, default='')
    active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['ordering', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Country(models.Model):
    name = models.CharField(max_length=100)
    iso_code = models.CharField(max_length=10, unique=True)
    flag_emoji = models.CharField(max_length=10, blank=True, default='')
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Countries'
        ordering = ['name']
        indexes = [
            models.Index(fields=['iso_code']),
            models.Index(fields=['active']),
        ]

    def __str__(self):
        return f"{self.flag_emoji} {self.name}".strip()

class Region(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='regions')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, default='')
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'State / Region'
        verbose_name_plural = 'States / Regions'
        ordering = ['name']
        unique_together = ('country', 'name')

    def __str__(self):
        return f"{self.name} ({self.country.name})"

class StockStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    DRAFT = 'DRAFT', 'Draft'
    ARCHIVED = 'ARCHIVED', 'Archived'

class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    state = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    description = models.TextField(blank=True, default='')
    short_description = models.CharField(max_length=500, blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=12.00)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=5, default='USD')
    preview_image = models.ImageField(upload_to='previews/', null=True, blank=True)
    downloadable_file = models.FileField(upload_to='products/files/', null=True, blank=True)
    file_type = models.CharField(max_length=20, default='PSD', help_text='e.g. PSD, AI, PNG, PDF')
    file_size = models.CharField(max_length=20, default='15 MB')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    stock_status = models.CharField(max_length=20, choices=StockStatus.choices, default=StockStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.name} (${self.price})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        return self.sale_price if self.sale_price and self.sale_price < self.price else self.price

    @property
    def disclaimer(self):
        return (
            "⚠️ EDUCATIONAL DESIGN TEMPLATE ONLY\n"
            "• SAMPLE TEMPLATE\n"
            "• NOT A GOVERNMENT DOCUMENT\n"
            "• NOT VALID FOR IDENTIFICATION OR REAL-WORLD USE"
        )

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to='previews/extra/')
    caption = models.CharField(max_length=200, blank=True, default='')

    def __str__(self):
        return f"Image for {self.product.name}"
