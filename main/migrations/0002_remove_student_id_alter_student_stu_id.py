# Generated by Django 4.2.4 on 2023-08-06 05:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='student',
            name='id',
        ),
        migrations.AlterField(
            model_name='student',
            name='stu_id',
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
    ]
