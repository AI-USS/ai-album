# Generated by Django 5.1 on 2024-09-03 11:28

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('surname', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'Person',
                'verbose_name_plural': 'People',
            },
        ),
        migrations.CreateModel(
            name='Photographic',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('awers', models.BinaryField(verbose_name='Awers')),
                ('rewers', models.BinaryField(null=True, verbose_name='Rewers')),
                ('colorized', models.BinaryField(null=True, verbose_name='Colorized Foto')),
                ('width', models.IntegerField(verbose_name='Width')),
                ('height', models.IntegerField(verbose_name='Height')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('format', models.TextField(blank=True, verbose_name='format')),
            ],
            options={
                'verbose_name': 'Photographic',
                'verbose_name_plural': 'Photographics',
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('keyword', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tags',
            },
        ),
        migrations.CreateModel(
            name='LearningPhotoFace',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('face', models.BinaryField(verbose_name='Face Blob')),
                ('coordinates', django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), size=4, verbose_name='Coordinates')),
                ('personid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='learning_photos', to='photo_gallery.person')),
                ('photographicid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='learning_faces', to='photo_gallery.photographic')),
            ],
            options={
                'verbose_name': 'Learning Photo Face',
                'verbose_name_plural': 'Learning Photo Faces',
            },
        ),
        migrations.CreateModel(
            name='PhotoVersion',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('file', models.BinaryField(verbose_name='Photo File')),
                ('format', models.CharField(max_length=10, verbose_name='File Format')),
                ('size', models.IntegerField(blank=True, null=True, verbose_name='File Size')),
                ('photographic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='photo_gallery.photographic')),
            ],
            options={
                'verbose_name': 'Photo Version',
                'verbose_name_plural': 'Photo Versions',
            },
        ),
        migrations.AddField(
            model_name='photographic',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='photographics', to='photo_gallery.tag'),
        ),
    ]
