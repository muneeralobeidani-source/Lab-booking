import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# إعداد قاعدة البيانات
def init_db():
    conn = sqlite3.connect('school_mobile_booking.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_name TEXT, location TEXT, grade TEXT, 
            subject TEXT, period TEXT, booking_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# واجهة التطبيق
st.set_page_config(page_title="حجز المرافق المدرسية", layout="centered")

st.title("📱 نظام حجز المختبر والصفوف")
st.markdown("---")

# نموذج إدخال البيانات
with st.form("booking_form"):
    teacher_name = st.text_input("اسم المعلم")
    location = st.selectbox("مكان الحجز", ["مختبر العلوم", "الصف الدراسي"])
    grade = st.select_slider("الصف", options=["5", "6", "7", "8", "9", "10", "11", "12"])
    subject = st.selectbox("المادة", ["علوم", "فيزياء", "كيمياء", "أحياء", "علوم وبيئة"])
    period = st.selectbox("الحصة", ["1", "2", "3", "4", "5", "6", "7", "8"])
    booking_date = st.date_input("التاريخ", date.today())
    
    submit = st.form_submit_button("تأكيد الحجز")

if submit:
    if teacher_name:
        conn = sqlite3.connect('school_mobile_booking.db')
        cursor = conn.cursor()
        
        # منع التكرار
        cursor.execute('''SELECT * FROM bookings WHERE location=? AND period=? AND booking_date=?''', 
                       (location, period, str(booking_date)))
        
        if cursor.fetchone():
            st.error(f"❌ عذراً، {location} محجوز مسبقاً في هذا الوقت!")
        else:
            cursor.execute('''INSERT INTO bookings (teacher_name, location, grade, subject, period, booking_date) 
                              VALUES (?, ?, ?, ?, ?, ?)''', 
                           (teacher_name, location, grade, subject, period, str(booking_date)))
            conn.commit()
            st.success("✅ تم تسجيل حجزك بنجاح!")
        conn.close()
    else:
        st.warning("⚠️ يرجى إدخال اسم المعلم")

# عرض الجدول
st.markdown("### 📋 الحجوزات الحالية")
conn = sqlite3.connect('school_mobile_booking.db')
df = pd.read_sql_query("SELECT teacher_name as 'المعلم', location as 'المكان', grade as 'الصف', subject as 'المادة', period as 'الحصة', booking_date as 'التاريخ' FROM bookings", conn)
st.dataframe(df, use_container_width=True)
conn.close()