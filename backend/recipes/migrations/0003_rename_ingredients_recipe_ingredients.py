# Generated by Django 3.2.18 on 2023-04-22 21:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recipe',
            old_name='ingredients',
            new_name='Ingredients',
        ),
    ]
