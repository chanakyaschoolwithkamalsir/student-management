# Generated by Django 4.2.4 on 2023-08-06 05:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_student_id_alter_student_stu_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='stu_id',
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
