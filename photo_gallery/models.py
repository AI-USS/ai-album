from django.db import models
from django.contrib.postgres.fields import ArrayField


# Create your models here.

class Photographic(models.Model):
    
    id = models.AutoField(primary_key=True)
    awers = models.BinaryField(verbose_name="Awers")
    rewers = models.BinaryField(verbose_name="Rewers", null=True)
    colorized = models.BinaryField(verbose_name="Colorized Foto", null=True)
    width = models.IntegerField(verbose_name="Width")
    height = models.IntegerField(verbose_name="Height")
    description = models.TextField(verbose_name="Description", blank=True, null=True)
    format = models.TextField(verbose_name="format", blank=True)
    
    tags = models.ManyToManyField('Tag', related_name='photographics', blank=True)

    def __str__(self):
        return f"Photographic {self.id} - {self.description[:20]}"

    class Meta:
        verbose_name = "Photographic"
        verbose_name_plural = "Photographics"

class Tag(models.Model):
    id = models.AutoField(primary_key=True)
    keyword = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.keyword

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

class Person(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} {self.surname}"

    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "People"

class LearningPhotoFace(models.Model):
    id = models.AutoField(primary_key=True)
    face = models.BinaryField(verbose_name="Face Blob")
    personid = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='learning_photos')
    photographicid = models.ForeignKey('Photographic', on_delete=models.CASCADE, related_name='learning_faces')
    coordinates = ArrayField(
        models.FloatField(),
        size=4,
        verbose_name="Coordinates"
    )

    def __str__(self):
        return f"LearningPhotoFace {self.id} - Person: {self.personid} - Photo: {self.photographicid}"

    class Meta:
        verbose_name = "Learning Photo Face"
        verbose_name_plural = "Learning Photo Faces"

class PhotoVersion(models.Model):
    id = models.AutoField(primary_key=True)
    photographic = models.ForeignKey('Photographic', on_delete=models.CASCADE, related_name='versions')
    file = models.BinaryField(verbose_name="Photo File")
    format = models.CharField(max_length=10, verbose_name="File Format")
    size = models.IntegerField(verbose_name="File Size", blank=True, null=True)

    def __str__(self):
        return f"PhotoVersion {self.id} - Format: {self.format} - Photo ID: {self.photographic.id}"

    class Meta:
        verbose_name = "Photo Version"
        verbose_name_plural = "Photo Versions"
