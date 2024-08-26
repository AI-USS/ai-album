# Generated by Django 5.1 on 2024-08-27 13:30

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("photo_gallery", "0002_tag_photographic_tags"),
    ]

    operations = [
        migrations.CreateModel(
            name="Person",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("surname", models.CharField(max_length=100)),
            ],
            options={
                "verbose_name": "Person",
                "verbose_name_plural": "People",
            },
        ),
        migrations.CreateModel(
            name="LearningPhotoFace",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("face", models.BinaryField(verbose_name="Face Blob")),
                (
                    "coordinates",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.FloatField(),
                        size=4,
                        verbose_name="Coordinates",
                    ),
                ),
                (
                    "photographicid",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="learning_faces",
                        to="photo_gallery.photographic",
                    ),
                ),
                (
                    "personid",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="learning_photos",
                        to="photo_gallery.person",
                    ),
                ),
            ],
            options={
                "verbose_name": "Learning Photo Face",
                "verbose_name_plural": "Learning Photo Faces",
            },
        ),
    ]
