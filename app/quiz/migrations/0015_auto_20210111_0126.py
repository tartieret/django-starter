# Generated by Django 3.0.11 on 2021-01-11 01:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0014_auto_20210110_2334'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Essay_Question',
            new_name='EssayQuestion',
        ),
        migrations.RenameModel(
            old_name='TF_Question',
            new_name='TFQuestion',
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(blank=True, max_length=250, null=True, unique=True, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='subcategory',
            name='name',
            field=models.CharField(blank=True, max_length=250, null=True, verbose_name='Name'),
        ),
    ]