# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donhang', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chitietdonhang',
            name='size',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='chitietdonhang',
            name='color',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]

