# Generated by Django 5.1.3 on 2024-11-27 11:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0002_alter_cartitem_size'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cartitem',
            name='size',
        ),
    ]
