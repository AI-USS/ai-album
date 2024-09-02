from django.db import models
import base64
from django.utils.safestring import mark_safe
# Create your models here.

class Photographic(models.Model):
    
    id = models.AutoField(primary_key=True)
    awers = models.BinaryField(verbose_name="Awers", editable=True)
    rewers = models.BinaryField(verbose_name="Rewers")
    colorized = models.BinaryField(verbose_name="Colorized Foto")
    width = models.IntegerField(verbose_name="Width")
    height = models.IntegerField(verbose_name="Height")
    description = models.TextField(verbose_name="Description", blank=True, null=True)

    def __str__(self):
        return f"Photographic {self.id} - {self.description[:20]}"
    
    @property
    def get_awers(self):
        image_data = base64.b64encode(self.awers).decode()
        return image_data
    
    def admin_awers_image_tag(self):
        return mark_safe('<img src="data:image/jpg;base64,{}"width="100" height="auto'.format(base64.b64encode(self.awers).decode()))
    
    admin_awers_image_tag.short_description = "Awers_Photo"
    admin_awers_image_tag.allow_tags = True

    class Meta:
        verbose_name = "Photographic"
        verbose_name_plural = "Photographics"