# Align migration state with the existing SET_NULL model policy.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('photo_gallery', '0005_alter_photographic_rewers')]
    operations = [
        migrations.AlterField(
            model_name="learningphotoface",
            name="personid",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="learning_photos",
                to="photo_gallery.person",
            ),
        ),
    ]
