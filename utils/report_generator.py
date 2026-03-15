import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from datetime import datetime
import os

def generate_pdf_report(name, age, phone, disease, description, precautions, workouts, diets, medications, vitals, bmi, file_path):
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    styleN = styles['BodyText']
    styleH = styles['Heading1']
    styleH2 = styles['Heading2']

    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    
    story = []
    
    # Title
    story.append(Paragraph("DocBuddy Health Report", styleH))
    story.append(Spacer(1, 12))
    
    # Patient Details
    story.append(Paragraph("Patient Details", styleH2))
    story.append(Paragraph(f"Patient Name : <b>{name.title()}</b>", styleN))
    story.append(Paragraph(f"Patient Age : <b>{age} Years</b>", styleN))
    if phone:
        story.append(Paragraph(f"Contact Number : <b>{phone}</b>", styleN))
    story.append(Paragraph(f"Report Generated On : <b>{current_time}</b>", styleN))
    story.append(Spacer(1, 12))

    # Vitals
    story.append(Paragraph("Patient Vitals & BMI", styleH2))
    if vitals:
        story.append(Paragraph(f"SpO2: <b>{vitals.get('spo2', 'N/A')}%</b>", styleN))
        story.append(Paragraph(f"Body Temp: <b>{vitals.get('temp', 'N/A')}°F</b>", styleN))
        story.append(Paragraph(f"Systolic BP: <b>{vitals.get('bp', 'N/A')}</b>", styleN))
    if bmi:
        story.append(Paragraph(f"Calculated BMI: <b>{bmi:.1f}</b>", styleN))
    story.append(Spacer(1, 12))

    # Results
    story.append(Paragraph("Health Assessment", styleH2))
    story.append(Paragraph(f"Predicted Disease : <b>{disease.title()}</b>", styleN))
    story.append(Paragraph(f"Description : <b>{description}</b>", styleN))
    story.append(Spacer(1, 12))

    # Lists
    def add_list_section(title, items, bullet='bullet'):
        if items is not None and len(items) > 0:
            story.append(Paragraph(title, styleH2))
            story.append(Spacer(1, 6))
            list_items = [ListItem(Paragraph(str(item), styleN)) for item in items if item]
            story.append(ListFlowable(list_items, bulletType=bullet))
            story.append(Spacer(1, 12))

    add_list_section("Precautions", precautions)
    add_list_section("Recommendations", workouts)
    add_list_section("Diets", diets)
    add_list_section("Medications", medications)

    doc.build(story)
    return file_path
