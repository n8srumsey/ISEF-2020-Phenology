# Generated by Django 3.1.5 on 2021-01-28 05:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_auto_20210109_0044'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='latitude',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='site',
            name='longitude',
            field=models.FloatField(default=0.0),
        ),
    ]
