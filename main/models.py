from django.db import models
from django.contrib.postgres.fields import ArrayField


# Create your models here.
class AboutPage(models.Model):
    about = models.TextField()

    def __str__(self):
        return self.about

class ContactPage(models.Model):
    address = models.TextField()
    contact_num = models.IntegerField()
    email = models.EmailField()

    def __str__(self):
        return self.address


class Student(models.Model):
    full_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=50)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    email = models.CharField(max_length=254)
    student_contact_number = models.CharField(max_length=10)
    parent_contact_number = models.CharField(max_length=10)
    date_of_birth = models.DateField()
    roll_no = models.BigIntegerField()
    medium = models.CharField(max_length=50)
    id = models.BigAutoField(primary_key=True)
    user_name = models.CharField(max_length=50)
    password = models.CharField(max_length=100)
    batch = models.IntegerField(blank=True, null=True)
    standard = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    std_code = models.IntegerField(blank=True, null=True)
    student_pic = models.BinaryField(blank=True, null=True)
    filepath = models.TextField(blank=True, null=True, default='data:image/jpeg;base64,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')

    class Meta:
        managed = True
        db_table = 'main_student'
    

class TestData(models.Model):
    id = models.BigAutoField(primary_key=True)
    test_date = models.DateField(blank=True, null=True)
    standard = models.IntegerField(blank=True, null=True)
    medium = models.TextField(blank=True, null=True)
    total_marks = models.IntegerField(blank=True, null=True)
    chapters = models.TextField(blank=True, null=True)
    subject = models.CharField(max_length=50, blank=True, null=True)
    test_type = models.CharField(max_length=50, blank=True, null=True)
    marks_filled = models.BooleanField(default=False)
    test_paper = models.BinaryField(blank=True, null=True)
    file_name = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'test_data'

class Notice(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    isPublic = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Teacher(models.Model):
    full_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=50)
    email = models.EmailField()
    contact_num = models.CharField(max_length=20)
    qualification = models.TextField()

    def __str__(self):
        return self.full_name


class ChapterMaster(models.Model):
    id = models.IntegerField(primary_key=True)
    chapter_name = models.TextField(blank=True, null=True)
    subject = models.TextField(blank=True, null=True)
    medium = models.TextField(blank=True, null=True)
    chapter_no = models.IntegerField(blank=True, null=True)
    std = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'chapter_master'


class StudentTestResults(models.Model):
    student_id = models.BigIntegerField()
    test_id = models.BigIntegerField()
    total_marks = models.IntegerField(blank=True, null=True)
    obtained = models.IntegerField(blank=True, null=True)
    batch = models.IntegerField(blank=True, null=True)
    created_ts = models.DateField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'student_test_results'
        unique_together = ('student_id', 'test_id')

class StandardMaster(models.Model):
    id = models.IntegerField(primary_key=True)
    std = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'standard_master'