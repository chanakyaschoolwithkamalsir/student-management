# Generated by Django 4.2.4 on 2023-08-06 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_remove_student_id_alter_student_stu_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='id',
            field=models.BigAutoField(auto_created=True, default=1, primary_key=True, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='student',
            name='stu_id',
            field=models.BigIntegerField(),
        ),
    ]
