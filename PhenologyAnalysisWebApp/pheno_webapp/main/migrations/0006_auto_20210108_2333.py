# Generated by Django 3.1.4 on 2021-01-09 07:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_auto_20210107_1642'),
    ]

    operations = [
        migrations.AlterField(
            model_name='site',
            name='sitename',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
