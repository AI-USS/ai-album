# Generated by Django 5.1 on 2024-08-28 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("photo_gallery", "0004_photoversion"),
    ]

    operations = [
        migrations.AddField(
            model_name="photographic",
            name="format",
            field=models.TextField(blank=True, verbose_name="format"),
        ),
        migrations.AlterField(
            model_name="photographic",
            name="colorized",
            field=models.BinaryField(null=True, verbose_name="Colorized Foto"),
        ),
        migrations.AlterField(
            model_name="photographic",
            name="rewers",
            field=models.BinaryField(null=True, verbose_name="Rewers"),
        ),
    ]
