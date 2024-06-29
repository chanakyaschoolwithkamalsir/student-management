from django.urls import path
from . import views
from .views import addTestAPI, SheetDownload, TopFiveStudents, GenerateReport, \
                    AllTestsDownload, TestResultDownload, SendReportWhatsapp
from . import backup_cron

urlpatterns = [
    path('', views.home, name="home"),
    path('about/', views.about, name="about"),
    path('contact/', views.contact, name="contact"),
    path('admin_panel/dashboard/', views.adminPanel, name="admin_panel"),
    path('admin_panel/login/', views.adminLogin, name="admin_login"),

    path('admin_panel/logout/', views.adminLogout, name="admin_logout"),
    path('student/login/', views.studentLogin, name="student_login"),
    path('admin_panel/add_student/', views.addStudent, name="add_student"),
    path('admin_panel/about/', views.adminAbout, name="admin_about"),
    path('admin_panel/update_about/<str:id>/', views.updateAbout, name="update_about"),

    path('admin_panel/contact/', views.adminContact, name="admin_contact"),
    path('admin_panel/update_contact/<str:id>/', views.updateContact, name="update_contact"),
    path('admin_panel/manage_students/', views.manageStudent, name="manage_students"),
    path('admin_panel/view_student/<int:id>/', views.viewStudent, name="view_student"),
    path('admin_panel/update_student/<str:id>/', views.updateStudent, name="update_student"),
    path('admin_panel/delete_student/<str:id>/', views.deleteStudent, name="delete_student"),
    path('admin_panel/add_notice/', views.addNotice, name="add_notice"),
    
    path('admin_panel/top_5_students/', views.view_top_5, name="top_5_students"),
    
    path('whatsapp_button/', views.whatsapp_button, name='whatsapp_button'),
    path('send_report/<int:id>/', views.send_report_whatsapp, name='send_report'),
    
    path('validate_image/', views.validate_image, name='validate_image'),
    
    path('admin_panel/add_test/', views.addTest, name="add_test"),

    path('admin_panel/addtestviaapi/', addTestAPI.as_view()),
    path('admin_panel/downloadsheet/', SheetDownload.as_view()),
    path('admin_panel/topfivestudents/', TopFiveStudents.as_view()),
    path('admin_panel/generatereport/', GenerateReport.as_view()),
    path('admin_panel/alltestsdownload/', AllTestsDownload.as_view()),
    path('admin_panel/testresultdownload/', TestResultDownload.as_view()),
    path('admin_panel/sendwhatsappfile/', SendReportWhatsapp.as_view()),


    path('admin_panel/manage_tests/', views.manageTest, name="manage_tests"),
    path('admin_panel/delete_test/<int:id>/', views.deleteTest, name="delete_test"),
    path('admin_panel/get_chapters/', views.get_chapters, name="get_chapters"),
    path('admin_panel/view_test/<int:test_id>/<int:standard>/<str:medium>/', views.view_test, name="view_test"),
    path('admin_panel/view_test_marks/<int:test_id>/<int:standard>/<str:medium>/', views.show_test_marks, name="view_test_marks"),
    # path('admin_panel/fill_marks/<int:test_id>/<int:standard>/<str:medium>/', views.fill_marks, name="fill_marks"),


    path('admin_panel/generate_pdf_report/<int:id>/', views.generate_pdf_report, name="generate_pdf_report"),
    path('admin_panel/download_test_paper/<int:test_id>/', views.download_test_paper, name="download_test_paper"),

    path('admin_panel/test_temp/', views.test_temp, name="test_temp"),
    path('admin_panel/test_code/', views.test_temp_filtered, name="test_code"),
    
    path('admin_panel/manage_notices/', views.manageNotices, name="manage_notices"),
    path('admin_panel/delete_notice/<str:id>/', views.deleteNotice, name="delete_notice"),
    path('admin_panel/update_notice/<str:id>/', views.updateNotice, name="update_notice"),

    path('admin_panel/add_teacher/', views.addTeacher, name="add_teacher"),
    path('admin_panel/manage_teacher/', views.manageTeachers, name="manage_teachers"),
    path('admin_panel/delete_teacher/<str:id>/', views.deleteTeacher, name="delete_teacher"),

    path('student/dashboard/', views.studentDashboard, name="student_dashboard"),
    path('student/logout/', views.studentLogout, name="student_logout"),
    path('student/update_teacher/<str:id>/', views.updateFaculty, name="update_teacher"),
    path('student/view_notices/', views.viewNotices, name="view_notices"),
    path('student/student_settings/', views.studentSettings, name="student_settings"),
    
    path('backup/', backup_cron.backup_db, name='backup')
]