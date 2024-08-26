from django.db import models

# Create your models here.

class Photographic(models.Model):
    
    id = models.AutoField(primary_key=True)
    awers = models.BinaryField(verbose_name="Awers")
    rewers = models.BinaryField(verbose_name="Rewers")
    colorized = models.BinaryField(verbose_name="Colorized Foto")
    width = models.IntegerField(verbose_name="Width")
    height = models.IntegerField(verbose_name="Height")
    description = models.TextField(verbose_name="Description", blank=True, null=True)

    def __str__(self):
        return f"Photographic {self.id} - {self.description[:20]}"

    class Meta:
        verbose_name = "Photographic"
        verbose_name_plural = "Photographics"