# Generated by Django 3.0.11 on 2020-11-22 01:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0002_auto_20201122_0049'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ['category'], 'verbose_name': 'Category', 'verbose_name_plural': 'Categories'},
        ),
        migrations.AlterModelOptions(
            name='subcategory',
            options={'ordering': ['sub_category'], 'verbose_name': 'Sub-Category', 'verbose_name_plural': 'Sub-Categories'},
        ),
    ]