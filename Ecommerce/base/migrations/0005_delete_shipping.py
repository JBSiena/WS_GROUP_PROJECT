# Generated by Django 5.1.3 on 2024-11-17 18:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_remove_product_average_rating_delete_productreview'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Shipping',
        ),
    ]
