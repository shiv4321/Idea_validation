import streamlit as st
import requests
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import re

# === CONFIGURATION ===
GROQ_API_KEY = "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"
GROQ_MODEL = "llama-3.3-70b-versatile"
ADMIN_EMAIL = "bootandboost@gmail.com"

# === PAGE CONFIG ===
st.set_page_config(
    page_title="Business Report Generator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === CUSTOM CSS ===
st.markdown("""
    <style>
    .main {
        background-color: #E3F2FD;
    }
    .stApp {
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
    }
    h1, h2, h3 {
        color: #0288D1;
    }
    .stButton>button {
        background-color: #0288D1;
        color: white;
        border-radius: 10px;
        padding: 10px 24px;
        font-size: 16px;
        font-weight: bold;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #0277BD;
        box-shadow: 0 4px 8px rgba(2, 136, 209, 0.3);
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>select {
        border: 2px solid #81D4FA;
        border-radius: 8px;
        padding: 10px;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #0288D1;
        box-shadow: 0 0 5px rgba(2, 136, 209, 0.3);
    }
    div[data-testid="stExpander"] {
        background-color: white;
        border: 2px solid #81D4FA;
        border-radius: 10px;
        padding: 10px;
    }
    .success-box {
        background-color: #C8E6C9;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 10px 0;
    }
    .info-box {
        background-color: #B3E5FC;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #0288D1;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# === INDUSTRY & STATE OPTIONS ===
INDUSTRIES = [
    "Technology & Software", "E-commerce & Retail", "Healthcare & Wellness",
    "Education & EdTech", "Food & Beverage", "Manufacturing", 
    "Agriculture & Agritech", "Finance & FinTech", "Real Estate",
    "Consulting & Services", "Travel & Hospitality", "Other"
]

STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Delhi", "Other"
]

BUSINESS_STAGES = [
    "Idea Stage",
    "Early Stage (0-2 years)",
    "Growth Stage (2-5 years)",
    "Established (5+ years)"
]

# === QUERY GROQ API ===
def query_groq(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a business consultant expert. Generate detailed, professional business reports "
                    "with clear headings, subheadings, bullet points, and actionable insights. "
                    "Format your response with clear sections and professional language."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers)
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

# === SEND EMAIL WITH PDF ===
def send_email_with_pdf(pdf_filename, recipient_email, user_data):
    """
    Send email with PDF attachment to admin email
    """
    try:
        # SMTP Configuration - Reads from .streamlit/secrets.toml
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = st.secrets["SENDER_EMAIL"]
        sender_password = st.secrets["SENDER_PASSWORD"]
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"New Business Report Generated - {user_data['business_name']}"
        
        # Email body
        body = f"""
A new business report has been generated.

Client Details:
- Name: {user_data['full_name']}
- Business Name: {user_data['business_name']}
- Email: {user_data['email']}
- Phone: {user_data['phone']}
- Address: {user_data['address']}
- Industry: {user_data['industry']}
- State: {user_data['state']}
- Business Stage: {user_data['business_stage']}

Please find the attached business report PDF.

Best regards,
Business Report Generator System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF
        with open(pdf_filename, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(pdf_filename)}")
            msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        return True, "Email sent successfully"
    except Exception as e:
        return False, f"Email sending failed: {str(e)}"

# === GENERATE PDF REPORT ===
def generate_business_report(data, ai_analysis):
    # Clean business name for filename
    clean_business_name = re.sub(r'[^\w\s-]', '', data['business_name']).strip().replace(' ', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Startup_Idea_Assessment_Report_for_{clean_business_name}_{timestamp}.pdf"
    
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0288D1'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0288D1'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#0288D1'),
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=10
    )
    
    elements = []
    
    # Title Page
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("STARTUP IDEA ASSESSMENT<br/>&<br/>VALIDATION REPORT", title_style))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"Business: {data['business_name']}", ParagraphStyle(
        'Subtitle', parent=styles['Normal'], fontSize=14, alignment=TA_CENTER, textColor=colors.HexColor('#0288D1'), fontName='Helvetica-Bold'
    )))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(f"Prepared for: {data['full_name']}", ParagraphStyle(
        'Subtitle2', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, textColor=colors.HexColor('#555555')
    )))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", ParagraphStyle(
        'Date', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.HexColor('#777777')
    )))
    elements.append(PageBreak())
    
    # Contact Information Section
    elements.append(Paragraph("CONTACT INFORMATION", heading_style))
    contact_data = [
        ['Full Name:', data['full_name']],
        ['Email:', data['email']],
        ['Phone:', data['phone']],
        ['Address:', data['address']],
    ]
    
    contact_table = Table(contact_data, colWidths=[2*inch, 4*inch])
    contact_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E3F2FD')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#B3E5FC')),
    ]))
    elements.append(contact_table)
    elements.append(Spacer(1, 20))
    
    # Business Overview Section
    elements.append(Paragraph("BUSINESS OVERVIEW", heading_style))
    overview_data = [
        ['Business Name:', data['business_name']],
        ['Industry:', data['industry']],
        ['State of Operation:', data['state']],
        ['Business Stage:', data['business_stage']],
    ]
    if data.get('udyam_number'):
        overview_data.append(['Udyam Registration:', data['udyam_number']])
    if data.get('website'):
        overview_data.append(['Website:', data['website']])
    
    overview_table = Table(overview_data, colWidths=[2*inch, 4*inch])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E3F2FD')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#B3E5FC')),
    ]))
    elements.append(overview_table)
    elements.append(Spacer(1, 20))
    
    # Business Goals Section
    if data['business_goals']:
        elements.append(Paragraph("BUSINESS GOALS & CUSTOMIZATION", heading_style))
        elements.append(Paragraph(data['business_goals'], normal_style))
        elements.append(Spacer(1, 20))
    
    # Competitive Advantage Section
    if data.get('competitive_advantage'):
        elements.append(Paragraph("COMPETITIVE ADVANTAGE & UNIQUE SELLING PROPOSITION", heading_style))
        elements.append(Paragraph(data['competitive_advantage'], normal_style))
        elements.append(Spacer(1, 20))
    
    # Additional Information
    if data.get('additional_info'):
        elements.append(Paragraph("ADDITIONAL DETAILS", heading_style))
        elements.append(Paragraph(data['additional_info'], normal_style))
        elements.append(Spacer(1, 20))
    
    # AI Analysis Section
    elements.append(PageBreak())
    elements.append(Paragraph("AI-GENERATED BUSINESS ANALYSIS", heading_style))
    elements.append(Spacer(1, 12))
    
    # Parse AI response
    lines = ai_analysis.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            elements.append(Spacer(1, 6))
        elif line.startswith('###'):
            heading_text = line.replace('###', '').strip()
            elements.append(Paragraph(heading_text, subheading_style))
        elif line.startswith('##'):
            heading_text = line.replace('##', '').strip()
            elements.append(Paragraph(heading_text, heading_style))
        elif line.startswith('#'):
            heading_text = line.replace('#', '').strip()
            elements.append(Paragraph(heading_text, heading_style))
        elif line.startswith(('- ', '* ', '• ')):
            bullet_text = line[2:].strip()
            elements.append(Paragraph(f"• {bullet_text}", normal_style))
        elif line.startswith(tuple(f"{i}." for i in range(1, 10))):
            elements.append(Paragraph(line, normal_style))
        else:
            elements.append(Paragraph(line, normal_style))
    
    # Build PDF
    doc.build(elements)
    return filename

# === MAIN APP ===
def main():
    # Header
    st.markdown("""
        <h1 style='text-align: center; color: #0288D1; font-size: 48px;'>
            🚀 BUSINESS IDEA GENERATION & VALIDATION REPORT 🚀
        </h1>
        <p style='text-align: center; color: #0277BD; font-size: 18px;'>
            Welcome! I'll help you create a comprehensive business report.
        </p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Initialize session state
    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False
    
    # Create form
    with st.form("business_form"):
        # 1. Personal Information
        st.markdown("### 📋 1. Personal Information")
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name *", placeholder="Enter your full name")
            email = st.text_input("Email Address *", placeholder="your.email@example.com")
        with col2:
            phone = st.text_input("Phone Number *", placeholder="+91 XXXXXXXXXX")
        
        address = st.text_area("Address *", placeholder="Enter your complete address", height=80)
        
        st.markdown("---")
        
        # 2. Business Information
        st.markdown("### 💼 2. Business Information")
        col3, col4 = st.columns(2)
        with col3:
            business_name = st.text_input("Business Name *", placeholder="Your business/startup name")
            business_stage = st.selectbox("Business Stage *", BUSINESS_STAGES)
        with col4:
            udyam_number = st.text_input("Udyam Registration Number (Optional)", placeholder="UDYAM-XX-00-1234567")
            website = st.text_input("Website (Optional)", placeholder="https://yourbusiness.com")
        
        st.markdown("---")
        
        # 3. Industry & Location
        st.markdown("### 🏭 3. Industry & Location Details")
        col5, col6 = st.columns(2)
        with col5:
            industry = st.selectbox("Preferred Industry *", INDUSTRIES)
        with col6:
            state = st.selectbox("State of Operation *", STATES)
        
        st.markdown("---")
        
        # 4. Business Goals
        st.markdown("### 🎯 4. Business Goals & Customization")
        business_goals = st.text_area(
            "Describe your business idea, goals, target audience, and preferences *",
            placeholder="Tell us about your business vision, target market, unique value proposition...",
            height=150
        )
        
        st.markdown("---")
        
        # 5. Competitive Advantage
        st.markdown("### 💡 5. Competitive Advantage & Unique Selling Proposition")
        competitive_advantage = st.text_area(
            "What makes your business unique? (Optional)",
            placeholder="Describe your competitive advantages, unique features, innovation, or what sets you apart from competitors...",
            height=120
        )
        
        st.markdown("---")
        
        # 6. Additional Details
        st.markdown("### 📝 6. Additional Details")
        additional_info = st.text_area(
            "Additional Information (Optional)",
            placeholder="DPIIT recognition status, specific market focus, funding goals, etc.",
            height=100
        )
        
        st.markdown("---")
        
        # Submit button
        col_center = st.columns([1, 2, 1])
        with col_center[1]:
            submit_button = st.form_submit_button("🚀 Generate Business Report", use_container_width=True)
    
    # Process form submission
    if submit_button:
        # Enhanced validation - check all mandatory fields
        validation_errors = []
        
        if not full_name or not full_name.strip():
            validation_errors.append("Full Name is required")
        if not email or not email.strip():
            validation_errors.append("Email Address is required")
        if not phone or not phone.strip():
            validation_errors.append("Phone Number is required")
        if not address or not address.strip():
            validation_errors.append("Address is required")
        if not business_name or not business_name.strip():
            validation_errors.append("Business Name is required")
        if not business_goals or not business_goals.strip():
            validation_errors.append("Business Goals & Customization is required")
        
        if validation_errors:
            st.error("⚠️ Please fill in all required fields (marked with *):")
            for error in validation_errors:
                st.error(f"   • {error}")
            return
        
        # Collect data
        data = {
            'full_name': full_name.strip(),
            'email': email.strip(),
            'phone': phone.strip(),
            'address': address.strip(),
            'business_name': business_name.strip(),
            'business_stage': business_stage,
            'udyam_number': udyam_number,
            'website': website,
            'industry': industry,
            'state': state,
            'business_goals': business_goals.strip(),
            'competitive_advantage': competitive_advantage.strip() if competitive_advantage else None,
            'additional_info': additional_info
        }
        
        # Show progress
        with st.spinner("🤖 Generating AI Analysis... Please wait..."):
            # Create prompt for AI
            competitive_adv_text = f"\n\nCompetitive Advantage:\n{data['competitive_advantage']}" if data.get('competitive_advantage') else ""
            
            prompt = f"""
Generate a comprehensive Business Idea Generation & Validation Report for the following business:

Business Details:
- Business Name: {data['business_name']}
- Owner: {data['full_name']}
- Industry: {data['industry']}
- Location: {data['state']}
- Business Stage: {data['business_stage']}

Business Goals:
{data['business_goals']}{competitive_adv_text}

Additional Information:
{data.get('additional_info', 'None provided')}

Please provide a detailed report with the following sections:
1. Executive Summary
2. Market Analysis for {data['industry']} in {data['state']}
3. Business Viability Assessment
4. Target Audience Analysis
5. Competitive Landscape
6. Revenue Model Suggestions
7. Key Success Factors
8. Potential Challenges & Risks
9. Recommendations & Next Steps

Use clear headings (##), subheadings (###), bullet points, and professional language.
"""
            
            # Get AI analysis
            ai_analysis = query_groq(prompt)
        
        if "Error" in ai_analysis:
            st.error(f"❌ {ai_analysis}")
            return
        
        # Generate PDF
        with st.spinner("📄 Generating PDF Report..."):
            try:
                filename = generate_business_report(data, ai_analysis)
                
                # Send email to admin
                with st.spinner("📧 Sending copy to admin..."):
                    email_success, email_message = send_email_with_pdf(filename, ADMIN_EMAIL, data)
                    if not email_success:
                        st.warning(f"⚠️ PDF generated but email delivery failed: {email_message}")
                
                # Success message
                st.markdown("""
                    <div class='success-box'>
                        <h2 style='color: #2E7D32; margin: 0;'>✅ Success!</h2>
                        <p style='color: #1B5E20; margin: 10px 0 0 0;'>
                            Your business report has been successfully generated!
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                #if email_success:
                 #   st.success(f"📧 A copy has been sent to {ADMIN_EMAIL}")
                
                # Download button
                with open(filename, "rb") as file:
                    st.download_button(
                        label="📥 Download Business Report",
                        data=file,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                # Show AI Analysis preview
                with st.expander("👀 Preview AI Analysis", expanded=True):
                    st.markdown(ai_analysis)
                
                # Cleanup
                if os.path.exists(filename):
                    os.remove(filename)
                
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
