# Generated by Django 3.0.11 on 2020-12-08 21:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0005_category_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitting',
            name='mode',
            field=models.CharField(choices=[('study', 'Study'), ('exam', 'Exam')], default='study', max_length=10, verbose_name='Mode'),
        ),
    ]
