#https://github.com/Jyes18/school-management

from io import BytesIO
import json, selenium, sys, cv2, shutil
import os, time
import django
from django.http import JsonResponse
from django.shortcuts import render, redirect
import pandas as pd, numpy as np

from django.db.models import Q
from django.utils import timezone

# from main.commonMethods import get_whatsapp_driver
from .models import AboutPage, ContactPage, Student, Notice, Teacher, TestData,\
                    ChapterMaster, StudentTestResults, StandardMaster
from django.views.decorators.csrf import csrf_protect
from django.db import connection
from .forms import StudentTestResultsForm  

from django.http import HttpResponse
from fpdf import FPDF
from .loggers import logger
from .commonMethods import send_whatsapp_file

from datetime import datetime

import matplotlib.pyplot as plt
import seaborn as sns

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service

from rest_framework.views import APIView


import warnings
warnings.filterwarnings("ignore")

driver = None

# from PyPDF2 import PdfFileMerger, PdfReader, PdfWriter

# def add_watermark(pdf_file, watermark, merged):
#     with open(pdf_file, "rb") as input_file, open(watermark, "rb") as watermark_file:
#         input_pdf = PdfReader(input_file)
#         watermark_pdf = PdfReader(watermark_file)
#         watermark_page = watermark_pdf.pages[0]

#         output = PdfWriter()
#         for i in range(input_pdf.getNumPages()):
#             pdf_page = input_pdf.pages[i]
#             pdf_page.mergePage(watermark_page)
#             output.addPage(pdf_page)

#         with open(merged, "wb") as merged_file:
#             output.write(merged_file)
    
#     os.remove(pdf_file)

class PDF(FPDF):

    # def header(self):
    #     # Replace this with the path to your logo image
        # logo_path = 'static/images/kamal_sir_logo_cdr.png'
    #     self.set_font('Arial', 'B', 12)
    #     self.set_text_color(0, 0, 0)
        
    #     # Center-align the logo
    #     logo_width = 100  # Adjust the width as needed
    #     self.image(logo_path, self.w / 2 - logo_width / 2, 10, logo_width)
    #     self.ln(70)

    def chapter_title(self, student):
        # Student info styling
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(30, 144, 255)  # Blue color
        self.cell(0, 10, f'Student: {student["full_name"]}   |   Standard: {student["standard"]}th {student["medium"]}', 0, 1, 'C')
        self.ln(10)
        self.set_font('Arial', '', 12)

def generate_pdf_report(request, id):
    logger.info(f"{id} - report generation starts")
    # Replace this with your database query or data retrieval logic
    query = f'''
            select str.id, student_id, test_id, td.total_marks, obtained, full_name, td.standard, td.medium,
            td.subject, td.test_date, td.chapters
            from sms_schema.student_test_results str
            left join sms_schema.main_student ms on ms.id=str.student_id
            left join sms_schema.test_data td on td.id=str.test_id
            where student_id={id} ORDER BY str.id desc'''
    
    student = Student.objects.get(id=id).full_name
    
    df = pd.read_sql_query(query, connection)
    logger.info(f"{id} - {df.shape[0]} data collected")
    df['chapters_list'] = df['chapters'].apply(lambda x: ", ".join(json.loads(x).keys()) if x else None)
    df['test_date'] = pd.to_datetime(df['test_date'])

    # Calculate the percentage of obtained marks for each subject
    df['percentage'] = (df['obtained'] / df['total_marks'] * 100).round(2)
    df['percentage %'] = df['percentage'].apply(lambda x: f"{x} %" if not pd.isna(x) else x)

    # List of unique subjects
    subjects = df['subject'].unique()

    logger.info(f"{id} - creating pdf object")
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    logo_path = 'static/images/kamal_sir_logo_cdr.png'
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 0, 0)
    
    # Center-align the logo
    logo_width = 100  # Adjust the width as needed
    pdf.image(logo_path, pdf.w / 2 - logo_width / 2, 10, logo_width)
    pdf.ln(70)
    
    logger.info(f"{id} - preparing student all data table")
    # Get student info
    student_info = df.iloc[0]
    pdf.chapter_title(student_info)
    record_table = [
    ['Subject', 'Test Date', 'Total', 'Obtained', 'Percentage'],
]

    col_widths = [40, 30, 30, 30, 30]

    for _, student_row in df.iterrows():
        record_table.append([
            student_row['subject'],
            student_row['test_date'].strftime('%d %b, %Y'),
            student_row['total_marks'],
            student_row['obtained'],
            student_row['percentage %']
        ])

    logger.info(f"{id} - start generating charts")
    # Create a separate bar chart for each subject using seaborn
    for subject in subjects:
        logger.info(f"{id} - {subject} chart is getting generated")
        subject_data = df[(df['subject'] == subject) & (df['full_name'] == student_row['full_name'])]
        subject_data['test_date'] = pd.to_datetime(subject_data['test_date'])
        subject_data['week_start'] = subject_data['test_date'].dt.to_period('W').apply(lambda r: r.start_time)

        num_test_dates = len(subject_data['week_start'])

        # Calculate a suitable chart width based on the number of test dates
        min_chart_width = 6
        max_chart_width = 12
        chart_width = max(min_chart_width, min(max_chart_width, num_test_dates * 0.8))

        # Get the current width of the PDF page (assuming pdf is your FPDF instance)
        pdf_page_width = pdf.w - pdf.l_margin - pdf.r_margin

        # Adjust the chart width to fit the PDF page if needed
        if chart_width * 30 > pdf_page_width:
            chart_width = pdf_page_width / 30

        plt.figure(figsize=(10, 6))  # Adjust width and height as needed
        sns.lineplot(x='week_start', y='percentage', data=subject_data, marker='o', color='b')
        plt.title(f'{subject.capitalize()} Performance Growth (%)')
        plt.xlabel('Week Start Date')
        plt.ylabel('Percentage of Obtained Marks')
        formatted_labels = [date.strftime('%d %b, %Y') for date in subject_data['week_start']]
        plt.xticks(subject_data['week_start'], formatted_labels, rotation=90)  # Rotate x-axis labels
        plt.tight_layout()
        # plt.show()

        # plt.figure(figsize=(10, 6))  # Adjust width and height as needed
        # sns.barplot(x=subject_data['week_start'], y=subject_data['percentage'], color='b')
        # plt.title('Simple Bar Chart')
        # plt.xlabel('Categories')
        # plt.ylabel('Values')
        # plt.xticks(rotation=45)  # Rotate x-axis labels for better visibility
        # plt.tight_layout()
        # plt.show()

        # Save the chart to a file
        chart_path = f'chart_{subject}.png'
        plt.savefig(chart_path, format='png', dpi=100)
        plt.close()

        # Embed the chart image into the PDF
        pdf.image(chart_path, x=pdf.w / 2 - chart_width * 30 / 2, w=chart_width * 30)  # Adjust factor for fine-tuning
        pdf.ln(10)
        # Delete the temporary chart file
        os.remove(chart_path)
        
        logger.info(f"{id} - {subject} chapter wise chart is getting generated")
        t = df[(df['subject']==subject) & (df['chapters'].notnull())]['chapters'].tolist()
        t = [json.loads(u) for u in t]
        chp = pd.DataFrame(t)
        chp.columns = set(chp.columns.astype(int))
        averages = chp.mean()

        plt.figure(figsize=(10, 6))
        ax = sns.barplot(x=averages.index, y=averages.values)

        plt.title(f'{subject} Average Score Per Chapter', fontsize=16)
        plt.xlabel('Chapters', fontsize=14)
        plt.ylabel('Average Value', fontsize=14)
        plt.xticks(rotation=45, fontsize=12)
        plt.yticks(fontsize=12)

        # Add data labels on the bars
        for p in ax.patches:
            ax.annotate(format(p.get_height(), '.2f'),
                        (p.get_x() + p.get_width() / 2., p.get_height()),
                        ha='center', va='center',
                        xytext=(0, 10),
                        textcoords='offset points',
                        fontsize=12)

        # Remove excess whitespace
        plt.tight_layout()
        # Save the chart to a file
        chart_path = f'chapter_wise_chart_{subject}_{id}.png'
        plt.savefig(chart_path, format='png', dpi=100)
        plt.close()
        pdf.image(chart_path, x=pdf.w / 2 - chart_width * 30 / 2, w=chart_width * 30)  # Adjust factor for fine-tuning
        pdf.ln(10)
        os.remove(chart_path)

    logger.info(f"{id} - adding data table")
    pdf.ln(10)
    # Header styling
    pdf.set_fill_color(0, 123, 255)  # Blue background
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(255, 255, 255)  # White text color
    for header_item, width in zip(record_table[0], col_widths):
        pdf.cell(width, 10, header_item, border=1, fill=True, ln=0, align='C')
    pdf.ln()

    # Data styling
    pdf.set_fill_color(240, 240, 240)  # Light gray background
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(0, 0, 0)  # Black text color
    for row in record_table[1:]:
        for data_item, width in zip(row, col_widths):
            pdf.cell(width, 10, str(data_item), border=1, fill=True, ln=0, align='C')
        pdf.ln()

    pdf.ln(10)

    folder_path = os.path.join(os.getcwd(), 'media', str(id))
    os.makedirs(folder_path, exist_ok=True)

    # Define the local PDF path
    local_pdf_path_no_wm = os.path.join(folder_path, f'{student}_report_{id}_without_watermark.pdf')
    pdf_file_name = f'{student}_report_{id}.pdf'
    local_pdf_path = os.path.join(folder_path, pdf_file_name)
    # Save the PDF to the specified local folder
    pdf.output(local_pdf_path_no_wm)
    
    # Prepare the HTTP response to provide the PDF as a download
    with open(local_pdf_path_no_wm, 'rb') as pdf_file:
        pdf_output_local = pdf_file.read()

    logger.info(f"{id} - saving pdf")
    pdf_output = pdf.output(dest='S').encode('latin1')
    
    # pdf_logo_path = 'static/images/kamal_sir_logo_cdr.pdf'
    # add_watermark(local_pdf_path_no_wm, pdf_logo_path, local_pdf_path)
    # logger.info(f"{id} - adding watermark")

    response = HttpResponse(pdf_output, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{pdf_file_name}"'
    return response
    # return redirect(f'http://127.0.0.1:8000/admin_panel/view_student/{id}/')


def is_driver_active(driver):
    try:
        # Execute a small command on the driver to check if it's still active
        driver.title
        return True
    except:
        return False

def get_whatsapp_driver():
    global driver

    if driver is None:
        options = webdriver.ChromeOptions()
        options.accept_insecure_certs = True
        options.add_argument("disable-infobars")
        # options.add_experimental_option('prefs',prefs)
        options.add_argument("--disable-extensions")
        options.add_argument('--no-sandbox')
        options.page_load_strategy = 'normal'
        if 'win' in sys.platform:
            options.binary_location ='C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
            chrome_driver_path = os.getcwd() + '\chromedriver\chromedriver.exe'
            print(chrome_driver_path)
        else:
            options.binary_location ='C:/Program Files/Google/Chrome/Application/chrome.exe'
            chrome_driver_path = os.getcwd() + '/chromedriver/chromedriver.exe'

        service = Service(executable_path=chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=options)

        url = 'https://web.whatsapp.com/'
        driver.get(url)
    
    return driver


def whatsapp_button(request):
    logger.info("connecting to whatsapp")
    try:
        driver = get_whatsapp_driver()
        logger.info(f"Automation URL name -> {driver.title}")
    except selenium.common.exceptions.NoSuchWindowException:
        driver = get_whatsapp_driver()
    except Exception as e:
        driver = get_whatsapp_driver()
        result = f"Error in getting WhatsApp Drivers"
        return HttpResponse(result)

    result = "Now Please Connect To WhatsApp Web !!!"
    return HttpResponse(result)


def send_report_whatsapp(request, id):
    # Your function logic here
    # For example, you can print the argument
    logger.info(f"Received argument: {id}")

    student_detail = Student.objects.get(id=id)
    mobile_number = student_detail.contact_num
    file_path = os.getcwd() + f"/media/{id}/test_report_{id}.pdf"
    if not bool(driver):
        whatsapp_button({})

    else:
        if driver.closed:
            whatsapp_button({})
            return redirect(f'http://127.0.0.1:8000/admin_panel/view_student/{id}/')

        try:
            search_box = driver.find_element('xpath', '/html/body/div[1]/div/div/div[4]/div/div[1]/div/div/div[2]/div/div[1]')
            search_box.send_keys(mobile_number)
            search_box.send_keys(Keys.RETURN)
            time.sleep(3)
        except selenium.common.exceptions.NoSuchWindowException:
            whatsapp_button({})
            return redirect(f'http://127.0.0.1:8000/admin_panel/view_student/{id}/')

        try:
            attachment_box = driver.find_element('xpath', '//div[@title = "Attach"]')
            attachment_box.click()
        except selenium.common.exceptions.NoSuchElementException:
            return HttpResponse(f"{mobile_number} is not on WhatsApp")
        except selenium.common.exceptions.NoSuchWindowException:
            whatsapp_button({})
            return redirect(f'http://127.0.0.1:8000/admin_panel/view_student/{id}/')

        try:
            image_box = driver.find_element('xpath', '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
            image_box.send_keys(file_path)
        except:
            return HttpResponse(f"{file_path} is not a file")

        time.sleep(3)

        send_button = driver.find_element('xpath', '/html/body/div[1]/div/div/div[3]/div[2]/span/div/span/div/div/div[2]/div/div[2]/div[2]/div/div')
        send_button.click()

    return redirect(f'http://127.0.0.1:8000/admin_panel/view_student/{id}/')


def home(request):
    publicNotices = Notice.objects.filter(isPublic = True)
    data = {"public_notices": publicNotices}
    return render(request, 'home.html', data)

def about(request):
    about_text = AboutPage.objects.all()
    data = {"aboutDetails": about_text}
    return render(request, 'about.html', data)

def contact(request):
    contact_text = ContactPage.objects.all()
    data = {"contactDetails": contact_text}
    return render(request, 'contact.html', data)

def adminPanel(request):
    if 'admin_user' in request.session:
        all_students = Student.objects.all()
        all_teachers = Teacher.objects.all()
        data = {'students': all_students, 'teachers': all_teachers}
        return render(request, 'admin/admin_panel.html', data)
    else:
        return redirect('admin_login')


def adminLogin(request):
    if request.method == 'POST':
        admin_email = request.POST['email']
        admin_pwd = request.POST['pwd']

        if admin_email == "admin@gmail.com" and admin_pwd == "admin@123":
            request.session['admin_user'] = admin_email
            return redirect('admin_panel')
        else:
            return redirect('admin_login')

    return render(request, 'admin/admin_login.html')

def adminLogout(request):
    del request.session['admin_user']
    return redirect('admin_login')


def adminAbout(request):
    about_details = AboutPage.objects.all()
    data = {"aboutDetails": about_details}
    return render(request, 'admin/admin_about.html', data)


def updateAbout(request, id):
    if request.method == 'POST':
        aboutText = request.POST['text']
        about_obj = AboutPage.objects.get(id = id)
        about_obj.about = aboutText
        about_obj.save()
    return redirect('admin_about')


def adminContact(request):
    contact_details = ContactPage.objects.all()
    data = {"contactDetails": contact_details} 
    return render(request, 'admin/admin_contact.html', data)


def updateContact(request, id):
    if request.method == 'POST':
        contactAddress = request.POST['address']
        contactEmail = request.POST['email']
        contactNumber = request.POST['contact']
        contact_obj = ContactPage.objects.get(id = id)
        contact_obj.address = contactAddress
        contact_obj.email = contactEmail
        contact_obj.contact_num = contactNumber
        contact_obj.save()
    return redirect('admin_contact')


def addStudent(request):
    # if 'admin_user' in request.session:
    if request.method == 'POST':
        print(request.POST)
        fullName = request.POST['full_name'] if request.POST['full_name'] not in [None, ''] else None
        gender = request.POST['gender'] if request.POST['gender'] not in [None, ''] else None
        roll_no = request.POST['roll_no'] if request.POST['roll_no'] not in [None, ''] else None
        parent_contact_number = request.POST['parent_contact_number'] if request.POST['parent_contact_number'] not in [None, ''] else None
        student_contact_number = request.POST['student_contact_number'] if request.POST['student_contact_number'] not in [None, ''] else None
        dob = request.POST['dob'] if request.POST['dob'] not in [None, ''] else None
        standard = request.POST['standard'] if request.POST['standard'] not in [None, ''] else None
        medium = request.POST['medium'] if request.POST['medium'] not in [None, ''] else None
        student_pic = request.FILES.get('student_pic') if request.FILES.get('student_pic') not in [None, ''] else None

        if bool(fullName) & bool(gender) & (bool(parent_contact_number) | bool(student_contact_number)) & bool(standard) & bool(medium):
            std_code = StandardMaster.objects.get(std=f"{standard}th {medium}").id

            add_student = Student(full_name=fullName, gender=gender, 
                                parent_contact_number=parent_contact_number,
                                student_contact_number=student_contact_number,
                                date_of_birth=dob, standard=standard, medium=medium, user_name=fullName.split(' ')[0], 
                                password=parent_contact_number, std_code=std_code, roll_no=roll_no)
            add_student.save()

            folder_path = os.path.join(os.getcwd(), 'media', str(add_student.id))
            os.makedirs(folder_path, exist_ok=True)
            if bool(student_pic):
                student_pic_content = student_pic.read()

                local_file_save = os.path.join(folder_path, f'{add_student.id}.'+student_pic.name.split('.')[-1])
                with open(local_file_save, 'wb') as file:
                    file.write(student_pic_content)

                add_student.student_pic = student_pic_content
                add_student.filepath=local_file_save
                add_student.save()
            else:
                shutil.copy('default_profile_pic.jpg', f'media/{add_student.id}/{add_student.id}.jpg')
        
        else:
            return render(request, 'temp/temp_add_student.html')

    return render(request, 'temp/temp_add_student.html')
    # else:
    #     return render(request, 'admin/admin_login.html')


def manageStudent(request):
    # if 'admin_user' in request.session:
    #     all_students = Student.objects.all()
    #     data = {"students": all_students}
    #     return render(request, 'admin/manage_students.html', data)

    # else:
    #     return render(request, 'admin/admin_login.html')
    if request.method == 'POST':
        selected_option = request.POST.get('selected-option')
        if bool(selected_option):
            std = int(selected_option.split('th')[0])
            medium = selected_option.split('th')[1]
            print(std, medium, StandardMaster.objects.get(std=selected_option).id)
            filtered_students = Student.objects.filter(std_code=StandardMaster.objects.get(std=selected_option).id)
            print(filtered_students)
        else:
            selected_option = 'All Students'
            filtered_students = Student.objects.all()
        data = {"students": filtered_students,
                "selected_option": selected_option}
        return render(request, "admin/manage_students.html", data)
    else:
        # Handle GET request (initial page load)
        # guj_11 = Student.objects.filter(standard=11, medium='Gujarati Medium')
        # guj_12 = Student.objects.filter(standard=12, medium='Gujarati Medium')
        # eng_11 = Student.objects.filter(standard=11, medium='English Medium')
        # eng_12 = Student.objects.filter(standard=12, medium='English Medium')
        # data = {"guj_11": guj_11,
        #         "guj_12": guj_12,
        #         "eng_11": eng_11,
        #         "eng_12": eng_12}
        

        filtered_students = Student.objects.all()
        data = {"students": filtered_students,
                "selected_option": "All Students"}

        return render(request, "admin/manage_students.html", data)


def viewStudent(request, id):
    # if 'admin_user' in request.session:
        query = f'''
                select str.id, student_id, test_id, td.total_marks, obtained, full_name, td.standard, td.medium,
                td.subject, td.test_date
                from sms_schema.student_test_results str
                left join sms_schema.main_student ms on ms.id=str.student_id
                left join sms_schema.test_data td on td.id=str.test_id
                where student_id={id} ORDER BY td.test_date DESC'''
        
        df = pd.read_sql_query(query, connection)
        df['percentage'] = (df['obtained'] / df['total_marks'] * 100).round(2)
        # all_tests = StudentTestResults.objects.filter(student_id=id)
        all_tests = df.to_dict('records')
        basic_analysis = {'biology': df[df['subject']=='Biology']['percentage'].mean().round(2),
                        'physics': df[df['subject']=='Physics']['percentage'].mean().round(2),
                        'chemistry': df[df['subject']=='Chemistry']['percentage'].mean().round(2),
                        'total_tests':len(df['test_id'].unique())}

        data = {"students": all_tests,
                "basic_analysis": basic_analysis,
                "id":id}
        # print(all_tests, data, "LLLLLLLll")
        return render(request, 'admin/view_student.html', data)
    
    # else:
    #     return render(request, 'admin/admin_login.html')


def manageTest(request):
    # if 'admin_user' in request.session:
    # all_tests = TestData.objects.all().order_by('-test_date', '-id')
    query = '''SELECT * FROM test_data ORDER BY (test_date, id) DESC'''
    df = pd.read_sql_query(query, connection)
    all_test_data = {"tests": df.to_dict('records')}
    return render(request, 'admin/manage_tests.html', all_test_data)

    # with connection.cursor() as cursor:
    #     cursor.execute("SELECT id, test_date, subject, standard, medium FROM test_data;")
    #     all_tests = cursor.fetchall()
    #     column_names = [desc[0] for desc in cursor.description]
    #     df = pd.DataFrame(all_tests, columns=column_names)
    #     # df.to_dict('records')
    #     data = {"tests": df.to_dict('records')}
    # print(data)
    # return render(request, 'admin/manage_tests.html', data)
    
    # else:
    #     return render(request, 'admin/admin_login.html')


def view_test(request, test_id, standard, medium):
    # if 'admin_user' in request.session:
    # med = {'guj':'Gujarati Medium', 'eng':'English Medium'}
    print(test_id, standard, medium, request.method)
    # try:
    #     test_instance = TestData.objects.get(id=test_id)
    # except TypeError as e:
    #     logger.info(f"{e} getting test")
    
    test_instance = TestData.objects.get(id=test_id)
    # query = f'''SELECT * FROM test_data WHERE test_id={test_id}'''
    
    student_list = Student.objects.filter(standard=standard, medium=medium)
    calculated_results = {}
    # print(student_list, "1111111111111")
    if request.method == 'POST':
        # print(form, '1111111111111')
        # if form.is_valid():
            # print(form, 'kkkkkkkkkkkk')
            # Save each student's marks to the StudentTestResults model
        # print(student_list, "llllllllllloooo")

        for student in student_list:
            correct_answers_key = 'correct_answers_' + str(student.id)
            incorrect_answers_key = 'incorrect_answers_' + str(student.id)

            logger.info(f"Test ID: {test_id}: Student ID: {student.id} - {request.POST.get(correct_answers_key, 0)}")
            logger.info(f"Test ID: {test_id}: Student ID: {student.id} - {request.POST.get(incorrect_answers_key, 0)}")

            if str(request.POST.get(correct_answers_key, 0)).isdigit() & \
                str(request.POST.get(incorrect_answers_key, 0)).isdigit():
                
                logger.info(f"Test ID: {test_id}: Student ID: {student.id} - {test_instance.test_type}")
                if test_instance.test_type in ['NEET', 'JEE']:
                    correct_answers = int(request.POST.get(correct_answers_key, 0)) * 4
                    incorrect_answers = int(request.POST.get(incorrect_answers_key, 0)) * 1
                    result = correct_answers - incorrect_answers
                elif test_instance.test_type == 'GUJCET':
                    correct_answers = int(request.POST.get(correct_answers_key, 0)) * 1
                    incorrect_answers = int(request.POST.get(incorrect_answers_key, 0)) * 0.25
                    result = correct_answers - incorrect_answers
                elif test_instance.test_type == 'Board':
                    correct_answers = None
                    incorrect_answers = None
                    result = None if request.POST.get(f"{student.id}")=='' else request.POST.get(f"{student.id}")
                else:
                    # Handle other test types here
                    correct_answers = None
                    incorrect_answers = None
                    result = None
            
            else:
                result = None

            logger.info(f'''Test ID: {test_id}: Student ID: {student.id} - {test_instance.test_type} \
                            Correct - {correct_answers}
                            Incorrect - {incorrect_answers}''')
            
            calculated_results[student.id] = result
                
            # marks_gained =  None if request.POST.get(f"{student.id}")=='' else request.POST.get(f"{student.id}")
            st_obj = StudentTestResults(student_id=student.id, test_id=test_instance.id, obtained=calculated_results[student.id],
                                        total_marks=test_instance.total_marks)
            try:
                st_obj.save()
            except django.db.utils.IntegrityError as e:
                logger.info(f"Error :- {e}")
                return render(request, 'admin/view_test.html', context)
        
        test_instance.marks_filled = True
        if isinstance(test_instance.chapters, dict):
            test_instance.chapters = None
        test_instance.save()

        # all_tests = TestData.objects.all('-id')
        # print(all_tests)
        # data = {"tests": all_tests}
        query = '''SELECT * FROM test_data ORDER BY (test_date, id) DESC'''
        df = pd.read_sql_query(query, connection)
        all_test_data = df.to_dict('records')
        data = {"tests": all_test_data}
        
        return render(request, 'admin/manage_tests.html', data)
    else:
        form = StudentTestResultsForm()

    context = {
        'test_instance': test_instance,
        'student_list': student_list,
        'calculated_results': calculated_results,
    }
    print(context, 'hhhhhhhhhhhhhhhhhhhhhhhhh')
    
    return render(request, 'admin/view_test.html', context)
    
    # else:
    #     return render(request, 'admin/admin_login.html')

@csrf_protect
def show_test_marks(request, test_id, standard, medium):
    logger.info(f'''Test ID: {test_id} - Standard: {standard} - Medium: {medium} -> show test marks''')
    test_instance = TestData.objects.get(id=test_id)
    
    query = f'''select ms.id as roll_no, full_name as name, ms.medium, ms.standard as std, test_id, str.obtained, td.total_marks, subject, test_type, test_date from 
                sms_schema.main_student ms 
                left join sms_schema.student_test_results str on str.student_id=ms.id
                left join sms_schema.test_data td on td.id=str.test_id
                WHERE test_id={test_id};'''

    test_data = pd.read_sql_query(query, connection)
    test_data['pct'] = (test_data['obtained'] / test_data['total_marks'] * 100).round(2)
    test_data = test_data.sort_values(by=['pct'], ascending=False)
    test_data['pct'] = test_data['pct'].fillna('-')
    test_data['obtained'] = test_data['obtained'].fillna('Absent')
    print(test_data)
    logger.info(f'''Test ID: {test_id} - Standard: {standard} - Medium: {medium} -> {test_data.shape[0]} Records''')
    context = {
        'test_instance': test_instance,
        'student_list': test_data.to_dict('records'),
    }
    
    return render(request, 'admin/view_test_marks.html', context)
        

@csrf_protect
def view_top_5(request):
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    query = f'''select full_name as name, ms.medium, ms.standard as std, test_id, str.obtained, td.total_marks, subject, test_type, test_date from 
                sms_schema.main_student ms 
                left join sms_schema.student_test_results str on str.student_id=ms.id
                left join sms_schema.test_data td on td.id=str.test_id'''

    data = pd.read_sql_query(query, connection)
    data['pct'] = (data['obtained'] / data['total_marks'] * 100).round(2)
    
    if start_date_str and end_date_str:
        start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d')
    else:
        current_date = timezone.now().date()

        start_date = current_date - timezone.timedelta(days=current_date.weekday())
        end_date = start_date + timezone.timedelta(days=6)

    total_test_within_dates = TestData.objects.filter(test_date__range=[start_date, end_date]).count()

    el = data[data['std']==11]
    el['present_tests'] = el['name'].map(el.groupby(['name'])['test_id'].count().to_dict())
    el['is_valid'] = np.where(el['present_tests']==el['present_tests'].max(), True, False)
    data_standard_11 = el[el['is_valid']==True].groupby(['name', 'medium'])['pct'].agg(['mean', 'count']).reset_index()
    data_standard_11.columns = ['name', 'medium', 'mean_pct', 'count_pct']
    data_standard_11 = data_standard_11.sort_values(by=['mean_pct'], ascending=False)
    top_5_standard_11 = data_standard_11[data_standard_11['mean_pct'].isin(data_standard_11['mean_pct'].head(5).tolist())].to_dict('records')


    tw = data[data['std']==12]
    tw['present_tests'] = tw['name'].map(tw.groupby(['name'])['test_id'].count().to_dict())
    tw['is_valid'] = np.where(tw['present_tests']==tw['present_tests'].max(), True, False)
    data_standard_12 = tw[tw['is_valid']==True].groupby(['name', 'medium'])['pct'].agg(['mean', 'count']).reset_index()
    data_standard_12.columns = ['name', 'medium', 'mean_pct', 'count_pct']
    data_standard_12 = data_standard_12.sort_values(by=['mean_pct'], ascending=False)
    top_5_standard_12 = data_standard_12[data_standard_12['mean_pct'].isin(data_standard_12['mean_pct'].head(5).tolist())].to_dict('records')

    result_data = {"top_5_standard_11": top_5_standard_11, 
                   "top_5_standard_12": top_5_standard_12,
                   "start_date": start_date.strftime('%d-%m-%Y'),
                   "end_date": end_date.strftime('%d-%m-%Y')}
    
    return render(request, 'admin/view_top_5.html', result_data)


@csrf_protect
def addTest(request):
    # if 'admin_user' in request.session:
    if request.method == 'POST':
        print(request.POST)
        standard = request.POST['standardDropdown']
        subject = request.POST['subjectDropdown']
        medium = request.POST['mediumDropdown']
        test_date = request.POST['test_date']
        chapters = request.POST.getlist('chapters')
        total_marks = request.POST['total_marks']
        test_paper = request.FILES.get('test_paper')

        print(request.POST)

        if bool(standard) & bool(medium) & bool(test_date):# & bool(test_paper):
            print('llllllllllllllllll', print(request.POST))
            file_name = None
            chap_list = None
            if bool(chapters):
                total_marks = sum([int(request.POST[f'marks_{i}']) for i in chapters if\
                                    request.POST[f'marks_{i}']!=''])
                chap_list = {int(i) : int(request.POST[f'marks_{i}']) for i in chapters if\
                                    request.POST[f'marks_{i}']!=''}
                chap_list = json.dumps(chap_list)

            add_test = TestData(standard=standard, test_date=test_date, 
                                chapters=chap_list, total_marks=total_marks, 
                                medium=medium, subject=subject, test_type=None,
                                test_paper=None, file_name=file_name)
            add_test.save()
        
        else:
            print(standard, medium, test_date, test_paper, 'llllll')

    # chapters_data = ChapterMaster.objects.filter(std=request.POST['standard'], medium=request.POST['medium'])
    # subjects = set(chapter.subject for chapter in chapters_data)
    # chapters_by_subject = {subject: [chapter.chapter_name for chapter in chapters_data if chapter.subject == subject] for subject in subjects}
    
    # return render(request, 'add_test.html', {'chapters_by_subject': chapters_by_subject})
    return render(request, 'admin/add_test.html')
    
    # else:
    #     return render(request, 'admin/admin_login.html')


# @csrf_protect
class addTestAPI(APIView):

    def post(self, request):

        test_file = request.FILES.get('file')
        standard = request.POST.get('standard', None)
        test_date = request.POST.get('date', None)
        total_marks = request.POST.get('total', None)
        medium = request.POST.get('medium', None)
        subject = request.POST.get('subject', None)

        response = {'msg': None,
                    'standard': standard,
                    'medium': medium,
                    'total': total_marks,
                    'date': test_date,
                    'filename': None,
                    'testId':None}

        if not bool(test_file):
            logger.info(f"file not uploaded")
            response.update({'msg': 'please upload file'})
            return JsonResponse(response, safe=False)

        filename = test_file.name
        data = pd.read_excel(test_file)
        # logger.info(data)
        response.update({'msg':'file uploaded',
                        'filename': filename})
        
        add_test_obj = TestData(standard=standard, test_date=pd.to_datetime(test_date, format="%d-%m-%Y"), 
                                chapters=None, total_marks=total_marks, 
                                medium=medium, subject=subject, test_type=None,
                                test_paper=None, file_name=filename)
        add_test_obj.save()

        response.update({'testId': add_test_obj.id})
        for record in data.to_dict('records'):
            student_id = Student.objects.get(roll_no = record['Roll Number'],
                                      full_name = record['Student']).id
            obtained = None if pd.isna(record['Obtained']) else record['Obtained']
            print(obtained, pd.isna(record['Obtained']))
            if not pd.isna(record['Obtained']):
                tmp = StudentTestResults(student_id=student_id, total_marks=total_marks,
                                    obtained=record['Obtained'], test_id=add_test_obj.id, 
                                    )
            else:
                tmp = StudentTestResults(student_id=student_id, total_marks=total_marks,
                                         test_id=add_test_obj.id, 
                                         )
            tmp.save()
        
        add_test_obj.marks_filled = True
        add_test_obj.save()

        return JsonResponse(response, safe=False)


# @csrf_protect
class SheetDownload(APIView):
    def get(self, request):
        standard = request.GET.get('standard', None)
        medium = request.GET.get('medium', None)

        response = {'msg': None,
                    'standard': None,
                    'medium': None}

        if bool(standard) & bool(medium):
            all_student = Student.objects.filter(standard=int(standard), medium=medium).\
                            values_list('roll_no', 'full_name',
                                         'parent_contact_number',)
            logger.info(all_student)
            df = pd.DataFrame.from_records(all_student, columns=['Roll Number', 'Student',
                                         'Contact Number'])
            
            df['Roll Number'] = df['Roll Number'].astype(int)
            df.sort_values('Roll Number', inplace=True)
            df['Obtained'] = ''
            df['Total'] = ''
            buffer = BytesIO()

            writer = pd.ExcelWriter(buffer, engine='xlsxwriter')
            df.to_excel(writer, index=False)
            writer.close()
            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            
            filename = f"{standard}th {medium} {datetime.now().strftime(r'%Y%m%d%H%M%S')}.xlsx"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

        else:
            response.update({'msg': 'please provide both standard and medium',
                            'standard': standard,
                            'medium': medium})
            return JsonResponse(response)

class AllTestsDownload(APIView):
    def get(self, request):
        test_data = TestData.objects.values_list('id', 'test_date', 'standard', 'medium', 'total_marks',
                                                 'subject', 'file_name')
        
        data = pd.DataFrame.from_records(test_data, columns=['Test ID', 'Test Date', 'Standard', 'Medium',
                                                             'Total Marks', 'Subject', 'Sheet Upload Name'])
        
        buffer = BytesIO()

        writer = pd.ExcelWriter(buffer, engine='xlsxwriter')
        data.to_excel(writer, index=False)
        writer.close()
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        filename = f"All Tests Data {datetime.now().strftime(r'%Y%m%d%H%M%S')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response


class TestResultDownload(APIView):
    def get(self, request):
        test_id = request.GET.get('test_id', None)

        if not bool(test_id):
            return JsonResponse({'msg': 'Test ID not provided'})
        
        query = f'''select test_id as "Test ID", full_name as Student, roll_no as "Roll Number",
                 ms.medium as Medium, ms.standard as Standard,
                 str.obtained as Obtained, td.total_marks as "Total Marks",
                subject as Subject, test_date as "Test Date" 
                from sms_schema.main_student ms 
                left join sms_schema.student_test_results str on str.student_id=ms.id
                left join sms_schema.test_data td on td.id=str.test_id
                WHERE td.id={test_id};'''

        data = pd.read_sql_query(query, connection)
        
        buffer = BytesIO()

        file_name = TestData.objects.get(id=int(test_id)).file_name

        writer = pd.ExcelWriter(buffer, engine='xlsxwriter')
        data.to_excel(writer, index=False)
        writer.close()
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        filename = f"Results - {file_name.split('.')[0]} {datetime.now().strftime(r'%Y%m%d%H%M%S')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response


@csrf_protect
def download_test_paper(request, test_id):
    logger.info(f"Test ID: {test_id} for downloading test paper")
    test_data = TestData.objects.get(id=test_id)
    test_paper = test_data.test_paper
    file_name = test_data.file_name

    if bool(test_paper):
        logger.info(f"Test ID: {test_id} - Sending file response as {file_name}")
        response = HttpResponse(test_paper, content_type = 'application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response
    else:
        logger.info(f"Test ID: {test_id} - No file to download")
        return HttpResponse(f"No File To Download")

@csrf_protect
def get_chapters(request):
    if request.method == 'GET':
        standard = request.GET.get('standard')
        medium = request.GET.get('medium')
        subject = request.GET.get('subject')

        if standard and medium and subject:
            chapters = ChapterMaster.objects.filter(std=standard, medium=medium, subject=subject).values('chapter_no', 'chapter_name').order_by('chapter_no')
            return JsonResponse({'chapters': list(chapters)})
        else:
            return JsonResponse({'chapters': []})

def updateStudent(request, id):
    if request.method == 'POST':
        student_obj = Student.objects.get(id=id)

        fullName = request.POST['full_name']
        gender = request.POST['gender']
        contactNum = request.POST['contact_number']
        dob = request.POST['dob'] or student_obj.date_of_birth
        course = request.POST['course'] or student_obj.course
        studentUserName = request.POST['stu_user_name']
        studentPassword = request.POST['stu_pwd']

        student_obj.full_name = fullName
        student_obj.gender = gender
        student_obj.contact_num = contactNum
        student_obj.date_of_birth = dob
        student_obj.course = course
        student_obj.user_name = studentUserName
        student_obj.password = studentPassword

        student_obj.save()
    return redirect('manage_students')

def deleteStudent(request, id):
    if 'admin_user' in request.session:
        stu_obj = Student.objects.get(id=id)
        stu_obj.delete()
    return redirect('manage_students')


def deleteTest(request, id):
    if 'admin_user' in request.session:
        test_obj = TestData.objects.get(id=id)
        test_obj.delete()
    return redirect('manage_tests')


def addNotice(request):
    if request.method == 'POST':
        noticeTitle = request.POST['notice_title']
        noticeContent = request.POST['notice_content']
        isPublic = request.POST['notice_status']

        add_notice = Notice.objects.create(title=noticeTitle, content=noticeContent, isPublic=isPublic)
        add_notice.save()
    return render(request, "admin/admin_notice.html")


def manageNotices(request):
    all_notices = Notice.objects.all()
    data = {'notices': all_notices}
    return render(request, 'admin/manage_notices.html', data)


def deleteNotice(request, id):
    if 'admin_user' in request.session:
        notice_obj = Notice.objects.get(id=id)
        notice_obj.delete()
    return redirect('manage_notices')

def updateNotice(request, id):
    if request.method == 'POST':
        title = request.POST['title']
        content = request.POST['content']
        status = request.POST['status']

        notice_obj = Notice.objects.get(id=id)
        notice_obj.title = title
        notice_obj.content = content
        notice_obj.isPublic = status

        notice_obj.save()
    return redirect('manage_notices')


def addTeacher(request):
    if request.method == 'POST':
        full_name = request.POST['full_name']
        gender = request.POST['gender']
        email = request.POST['email']
        contact_num = request.POST['contact_number']
        qualification = request.POST['qualification']

        add_teacher = Teacher.objects.create(full_name=full_name, gender=gender, email=email,contact_num=contact_num, qualification=qualification)
        add_teacher.save()
    return render(request, 'admin/add_teacher.html')

def manageTeachers(request):
    all_teachers = Teacher.objects.all()
    data = {"teachers": all_teachers}
    return render(request, 'admin/manage_teachers.html', data)

def deleteTeacher(request, id):
    teacher_obj = Teacher.objects.get(id=id)
    teacher_obj.delete()
    return redirect('manage_teachers')

def studentLogin(request):
    if 'student_user' not in request.session:
        if request.method == "POST":
            user_name = request.POST['userName']
            student_pwd = request.POST['stuPwd']

            stu_exists = Student.objects.filter(user_name=user_name, password=student_pwd).exists()
            if stu_exists:
                request.session['student_user'] = user_name
                return redirect('student_dashboard')

        return render(request, 'student/student_login.html')
    else:
        return redirect('student_dashboard')


def studentDashboard(request):
    if 'student_user' in request.session:
        student_in_session = Student.objects.get(user_name=request.session['student_user'])
        data  = {"student": student_in_session}
        return render(request, 'student/student_dashboard.html', data)
    else:
        return redirect('student_login')


def studentLogout(request):
    del request.session['student_user']
    return redirect('student_login')


def updateFaculty(request, id):
    if request.method == 'POST':
        full_name = request.POST['full_name']
        email = request.POST['email']
        contactNumber = request.POST['contact_number']
        gender = request.POST['gender']
        qualification = request.POST['qualification']

        teacher_obj = Teacher.objects.get(id=id)
        teacher_obj.full_name = full_name
        teacher_obj.email = email
        teacher_obj.contact_num = contactNumber
        teacher_obj.gender = gender
        teacher_obj.qualification = qualification
        teacher_obj.save()
    return redirect('manage_teachers')


def viewNotices(request):
    if 'student_user' in request.session:
        student_notice = Notice.objects.filter(isPublic = False)
        data = {"notices": student_notice}
        return render(request, 'student/view_notices.html', data)
    else:
        return redirect('student_login')


def studentSettings(request):
    if 'student_user' in request.session:
        student_obj = Student.objects.get(user_name = request.session['student_user'])
        data = {'student': student_obj}
        if request.method == 'POST':
            currentPwd = request.POST['current_pwd']
            new_pwd = request.POST['new_pwd']
            student_obj.password  =new_pwd
            student_obj.save() 
            return redirect('student_dashboard')      
        return render(request, "student/student_settings.html", data)
    else:
        return redirect('student_login')

@csrf_protect
def test_temp(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    print(start_date_str, end_date_str)
    query = f'''select full_name as name, ms.medium, ms.standard as std, test_id, str.obtained, td.total_marks, subject, test_type, test_date from 
                sms_schema.main_student ms 
                left join sms_schema.student_test_results str on str.student_id=ms.id
                left join sms_schema.test_data td on td.id=str.test_id'''

    data = pd.read_sql_query(query, connection)
    data['pct'] = (data['obtained'] / data['total_marks'] * 100).round(2)
    
    if start_date_str and end_date_str:
        start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d')
    else:
        current_date = timezone.now().date()

        start_date = current_date - timezone.timedelta(days=current_date.weekday())
        end_date = start_date + timezone.timedelta(days=6)

    total_test_within_dates = TestData.objects.filter(test_date__range=[start_date, end_date]).count()

    el = data[data['std']==11]
    el['present_tests'] = el['name'].map(el.groupby(['name'])['test_id'].count().to_dict())
    el['is_valid'] = np.where(el['present_tests']==el['present_tests'].max(), True, False)
    data_standard_11 = el[el['is_valid']==True].groupby(['name', 'medium'])['pct'].agg(['mean', 'count']).reset_index()
    data_standard_11.columns = ['name', 'medium', 'mean_pct', 'count_pct']
    data_standard_11 = data_standard_11.sort_values(by=['mean_pct'], ascending=False)
    top_5_standard_11 = data_standard_11[data_standard_11['mean_pct'].isin(data_standard_11['mean_pct'].head(5).tolist())].to_dict('records')


    tw = data[data['std']==12]
    tw['present_tests'] = tw['name'].map(tw.groupby(['name'])['test_id'].count().to_dict())
    tw['is_valid'] = np.where(tw['present_tests']==tw['present_tests'].max(), True, False)
    data_standard_12 = tw[tw['is_valid']==True].groupby(['name', 'medium'])['pct'].agg(['mean', 'count']).reset_index()
    data_standard_12.columns = ['name', 'medium', 'mean_pct', 'count_pct']
    data_standard_12 = data_standard_12.sort_values(by=['mean_pct'], ascending=False)
    top_5_standard_12 = data_standard_12[data_standard_12['mean_pct'].isin(data_standard_12['mean_pct'].head(5).tolist())].to_dict('records')

    result_data = {"top_5_standard_11": top_5_standard_11, 
                   "top_5_standard_12": top_5_standard_12,
                   "start_date": start_date.strftime('%d-%m-%Y'),
                   "end_date": end_date.strftime('%d-%m-%Y')}
    
    return render(request, 'temp/test_temp.html', result_data)

@csrf_protect
def test_temp_filtered(request):

    filtered_students = Student.objects.all()
    data = {"students": filtered_students}

    return render(request, "temp/temp_add_test.html", data)


def validate_image(request):
    if request.method == 'POST' and request.FILES.get('student_pic'):
        uploaded_image = request.FILES['student_pic']
        print(uploaded_image, request.FILES.get('student_pic'), "pppppppppppppppppppppppppppp")
        # You can save the uploaded image temporarily if needed
        # with open('temp_image.jpg', 'wb') as destination:
        #     for chunk in uploaded_image.chunks():
        #         destination.write(chunk)

        # Perform face detection on the uploaded image
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        image_data = uploaded_image.read()
        image_array = np.asarray(bytearray(image_data), dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))

        if len(faces) > 0:
            return JsonResponse({'is_valid': True})
        else:
            return JsonResponse({'is_valid': False})

    return JsonResponse({'error': 'Invalid request'}, status=400)


class TopFiveStudents(APIView):
    def get(self, request):
        
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        if start_date_str and end_date_str:
            start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            current_date = timezone.now().date()

            start_date = current_date - timezone.timedelta(days=current_date.weekday())
            end_date = start_date + timezone.timedelta(days=6)
        
        query = f'''select full_name as name, ms.medium, ms.standard as std, test_id, str.obtained, td.total_marks, subject, test_type, test_date from 
                    sms_schema.main_student ms 
                    left join sms_schema.student_test_results str on str.student_id=ms.id
                    left join sms_schema.test_data td on td.id=str.test_id
                    WHERE td.test_date BETWEEN '{start_date_str}' AND '{end_date_str}';'''
        print(query)

        data = pd.read_sql_query(query, connection)
        data['pct'] = (data['obtained'] / data['total_marks'] * 100).round(2)

        # total_test_within_dates = TestData.objects.filter(test_date__range=[start_date, end_date]).count()

        el = data[data['std']==11]
        el['present_tests'] = el['name'].map(el.groupby(['name'])['test_id'].count().to_dict())
        el['is_valid'] = np.where(el['present_tests']==el['present_tests'].max(), True, False)
        data_standard_11 = el[el['is_valid']==True].groupby(['name', 'medium'])['pct'].agg(['mean', 'count']).reset_index()
        data_standard_11.columns = ['name', 'medium', 'mean_pct', 'count_pct']
        data_standard_11 = data_standard_11.sort_values(by=['mean_pct'], ascending=False)
        top_5_standard_11 = data_standard_11[data_standard_11['mean_pct'].isin(data_standard_11['mean_pct'].head(5).tolist())].to_dict('records')

        print(top_5_standard_11)
        tw = data[data['std']==12]
        tw['present_tests'] = tw['name'].map(tw.groupby(['name'])['test_id'].count().to_dict())
        tw['is_valid'] = np.where(tw['present_tests']==tw['present_tests'].max(), True, False)
        data_standard_12 = tw[tw['is_valid']==True].groupby(['name', 'medium'])['pct'].agg(['mean', 'count']).reset_index()
        data_standard_12.columns = ['name', 'medium', 'mean_pct', 'count_pct']
        data_standard_12 = data_standard_12.sort_values(by=['mean_pct'], ascending=False)
        top_5_standard_12 = data_standard_12[data_standard_12['mean_pct'].isin(data_standard_12['mean_pct'].head(5).tolist())].to_dict('records')
        
        buffer = BytesIO()

        writer = pd.ExcelWriter(buffer, engine='xlsxwriter')
        pd.DataFrame(top_5_standard_11).to_excel(writer, index=False, sheet_name='11th Ranks')
        pd.DataFrame(top_5_standard_12).to_excel(writer, index=False, sheet_name='12th Ranks')
        writer.close()
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        filename = f"Student Ranks From {start_date_str} To {end_date_str} {datetime.now().strftime(r'%Y%m%d%H%M%S')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # return JsonResponse(result_data)
        return response
    
class GenerateReport(APIView):
    def get(self, request):
        # Replace this with your database query or data retrieval logic
        name = request.GET.get('name', None)
        standard = request.GET.get('standard', None)

        if not (bool(standard)) and (bool(name)):
            return JsonResponse({'msg': 'Provide name and standard'})

        try:
            student_id = Student.objects.get(standard=int(standard), full_name__iexact=name).id

        except Exception as e:
            logger.info(e)
            return JsonResponse({'msg': 'No student found with these roll_number and standard'})

        query = f'''
                select str.id, student_id, test_id, td.total_marks, obtained, full_name, td.standard, td.medium,
                td.subject, td.test_date, td.chapters
                from sms_schema.student_test_results str
                left join sms_schema.main_student ms on ms.id=str.student_id
                left join sms_schema.test_data td on td.id=str.test_id
                where student_id={student_id} ORDER BY str.id desc'''
        
        student = Student.objects.get(id=student_id).full_name
        
        df = pd.read_sql_query(query, connection)
        if df.empty:
            return JsonResponse({'msg': 'No marks records found'})

        logger.info(f"{student_id} - {df.shape[0]} data collected")
        df['chapters_list'] = df['chapters'].apply(lambda x: ", ".join(json.loads(x).keys()) if x else None)
        df['test_date'] = pd.to_datetime(df['test_date'])

        # Calculate the percentage of obtained marks for each subject
        df['percentage'] = (df['obtained'] / df['total_marks'] * 100).round(2)
        df['percentage %'] = df['percentage'].apply(lambda x: f"{x} %" if not pd.isna(x) else x)

        # List of unique subjects
        subjects = df['subject'].unique()

        logger.info(f"{student_id} - creating pdf object")
        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        logo_path = 'static/images/kamal_sir_logo_cdr.png'
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(0, 0, 0)
        
        # Center-align the logo
        logo_width = 100  # Adjust the width as needed
        pdf.image(logo_path, pdf.w / 2 - logo_width / 2, 10, logo_width)
        pdf.ln(70)
        
        logger.info(f"{student_id} - preparing student all data table")
        # Get student info
        student_info = df.iloc[0]
        pdf.chapter_title(student_info)
        record_table = [
        ['Subject', 'Test Date', 'Total', 'Obtained', 'Percentage'],
    ]

        col_widths = [40, 30, 30, 30, 30]

        for _, student_row in df.iterrows():
            record_table.append([
                student_row['subject'],
                student_row['test_date'].strftime('%d %b, %Y'),
                student_row['total_marks'],
                student_row['obtained'],
                student_row['percentage %']
            ])

        logger.info(f"{student_id} - start generating charts")
        # Create a separate bar chart for each subject using seaborn
        for subject in subjects:
            logger.info(f"{student_id} - {subject} chart is getting generated")
            subject_data = df[(df['subject'] == subject) & (df['full_name'] == student_row['full_name'])]
            subject_data['test_date'] = pd.to_datetime(subject_data['test_date'])
            subject_data['week_start'] = subject_data['test_date'].dt.to_period('W').apply(lambda r: r.start_time)

            num_test_dates = len(subject_data['week_start'])

            # Calculate a suitable chart width based on the number of test dates
            min_chart_width = 6
            max_chart_width = 12
            chart_width = max(min_chart_width, min(max_chart_width, num_test_dates * 0.8))

            # Get the current width of the PDF page (assuming pdf is your FPDF instance)
            pdf_page_width = pdf.w - pdf.l_margin - pdf.r_margin

            # Adjust the chart width to fit the PDF page if needed
            if chart_width * 30 > pdf_page_width:
                chart_width = pdf_page_width / 30

            plt.figure(figsize=(10, 6))  # Adjust width and height as needed
            sns.lineplot(x='week_start', y='percentage', data=subject_data, marker='o', color='b')
            plt.title(f'{subject.capitalize()} Performance Growth (%)')
            plt.xlabel('Week Start Date')
            plt.ylabel('Percentage of Obtained Marks')
            formatted_labels = [date.strftime('%d %b, %Y') for date in subject_data['week_start']]
            plt.xticks(subject_data['week_start'], formatted_labels, rotation=90)  # Rotate x-axis labels
            plt.tight_layout()
            # plt.show()

            # plt.figure(figsize=(10, 6))  # Adjust width and height as needed
            # sns.barplot(x=subject_data['week_start'], y=subject_data['percentage'], color='b')
            # plt.title('Simple Bar Chart')
            # plt.xlabel('Categories')
            # plt.ylabel('Values')
            # plt.xticks(rotation=45)  # Rotate x-axis labels for better visibility
            # plt.tight_layout()
            # plt.show()

            # Save the chart to a file
            chart_path = f'chart_{subject}.png'
            plt.savefig(chart_path, format='png', dpi=100)
            plt.close()

            # Embed the chart image into the PDF
            pdf.image(chart_path, x=pdf.w / 2 - chart_width * 30 / 2, w=chart_width * 30)  # Adjust factor for fine-tuning
            pdf.ln(10)
            # Delete the temporary chart file
            os.remove(chart_path)
            
            logger.info(f"{student_id} - {subject} chapter wise chart is getting generated")
            t = df[(df['subject']==subject) & (df['chapters'].notnull())]['chapters'].tolist()
            t = [json.loads(u) for u in t]
            chp = pd.DataFrame(t)
            chp.columns = set(chp.columns.astype(int))
            averages = chp.mean()

            plt.figure(figsize=(10, 6))
            ax = sns.barplot(x=averages.index, y=averages.values)

            plt.title(f'{subject} Average Score Per Chapter', fontsize=16)
            plt.xlabel('Chapters', fontsize=14)
            plt.ylabel('Average Value', fontsize=14)
            plt.xticks(rotation=45, fontsize=12)
            plt.yticks(fontsize=12)

            # Add data labels on the bars
            for p in ax.patches:
                ax.annotate(format(p.get_height(), '.2f'),
                            (p.get_x() + p.get_width() / 2., p.get_height()),
                            ha='center', va='center',
                            xytext=(0, 10),
                            textcoords='offset points',
                            fontsize=12)

            # Remove excess whitespace
            plt.tight_layout()
            # Save the chart to a file
            chart_path = f'chapter_wise_chart_{subject}_{student_id}.png'
            plt.savefig(chart_path, format='png', dpi=100)
            plt.close()
            pdf.image(chart_path, x=pdf.w / 2 - chart_width * 30 / 2, w=chart_width * 30)  # Adjust factor for fine-tuning
            pdf.ln(10)
            os.remove(chart_path)

        logger.info(f"{student_id} - adding data table")
        pdf.ln(10)
        # Header styling
        pdf.set_fill_color(0, 123, 255)  # Blue background
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(255, 255, 255)  # White text color
        for header_item, width in zip(record_table[0], col_widths):
            pdf.cell(width, 10, header_item, border=1, fill=True, ln=0, align='C')
        pdf.ln()

        # Data styling
        pdf.set_fill_color(240, 240, 240)  # Light gray background
        pdf.set_font('Arial', '', 12)
        pdf.set_text_color(0, 0, 0)  # Black text color
        for row in record_table[1:]:
            for data_item, width in zip(row, col_widths):
                pdf.cell(width, 10, str(data_item), border=1, fill=True, ln=0, align='C')
            pdf.ln()

        pdf.ln(10)

        folder_path = os.path.join(os.getcwd(), 'media', str(student_id))
        os.makedirs(folder_path, exist_ok=True)

        # Define the local PDF path
        local_pdf_path_no_wm = os.path.join(folder_path, f'{student}_report_{student_id}_without_watermark.pdf')
        pdf_file_name = f'{student}_report_{student_id}.pdf'
        local_pdf_path = os.path.join(folder_path, pdf_file_name)
        # Save the PDF to the specified local folder
        pdf.output(local_pdf_path_no_wm)
        
        # Prepare the HTTP response to provide the PDF as a download
        with open(local_pdf_path_no_wm, 'rb') as pdf_file:
            pdf_output_local = pdf_file.read()

        logger.info(f"{student_id} - saving pdf")
        pdf_output = pdf.output(dest='S').encode('latin1')
        
        # pdf_logo_path = 'static/images/kamal_sir_logo_cdr.pdf'
        # add_watermark(local_pdf_path_no_wm, pdf_logo_path, local_pdf_path)
        # logger.info(f"{id} - adding watermark")

        response = HttpResponse(pdf_output, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{pdf_file_name}"'
        return response
    

class SendReportWhatsapp(APIView):
    def post(self, request):
        # Your function logic here
        # For example, you can print the argument

        file = request.FILES.get('file')

        df = pd.read_excel(file)
        print(df)

        for record in df.to_dict('records'):
            student_detail = Student.objects.get(full_name=record['Student'])
            id = student_detail.id
            file_path = os.getcwd() + f"/media/{id}/test_report_{id}.pdf"
            if not bool(driver):
                whatsapp_button({})

            else:
                if driver.closed:
                    whatsapp_button({})
                    # return redirect(f'http://127.0.0.1:8000/admin_panel/view_student/{id}/')

                try:
                    search_box = driver.find_element('xpath', '/html/body/div[1]/div/div/div[4]/div/div[1]/div/div/div[2]/div/div[1]')
                    search_box.send_keys(record['Contact Number'])
                    search_box.send_keys(Keys.RETURN)
                    time.sleep(3)
                except selenium.common.exceptions.NoSuchWindowException:
                    whatsapp_button({})
                    return JsonResponse({'msg': 'Error'})

                try:
                    attachment_box = driver.find_element('xpath', '//div[@title = "Attach"]')
                    attachment_box.click()
                except selenium.common.exceptions.NoSuchElementException:
                    return HttpResponse(f"{record['Contact Number']} is not on WhatsApp")
                except selenium.common.exceptions.NoSuchWindowException:
                    whatsapp_button({})
                    return JsonResponse({'msg': 'Error'})

                try:
                    image_box = driver.find_element('xpath', '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                    image_box.send_keys(file_path)
                except:
                    return HttpResponse(f"{file_path} is not a file")

                time.sleep(3)

                send_button = driver.find_element('xpath', '/html/body/div[1]/div/div/div[3]/div[2]/span/div/span/div/div/div[2]/div/div[2]/div[2]/div/div')
                send_button.click()

        return JsonResponse({'msg': 'Messages Sent !'})
