# Generated by Django 3.1.4 on 2021-01-08 00:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20210107_1521'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='image_upload',
            field=models.ImageField(upload_to='<django.db.models.fields.related.ForeignKey>'),
        ),
    ]
