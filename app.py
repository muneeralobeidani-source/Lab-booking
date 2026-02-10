import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('school_booking_v2.db')
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

# إعدادات الصفحة
st.set_page_config(page_title="نظام حجز المرافق", layout="centered")
st.title("🏫 نظام حجز المختبر والصفوف")

# --- 2. قسم إضافة حجز جديد ---
st.header("➕ إضافة حجز جديد")
with st.form("add_form"):
    teacher_name = st.text_input("اسم المعلم")
    location = st.selectbox("مكان الحجز", ["مختبر العلوم", "الصف الدراسي"])
    
    # شكل جديد لاختيار الصف (مناسب للجوال)
    grade = st.select_slider("اختر الصف", options=["5", "6", "7", "8", "9", "10", "11", "12"])
    
    subject = st.selectbox("المادة", ["علوم", "فيزياء", "كيمياء", "أحياء", "علوم وبيئة"])
    period = st.select_slider("الحصة", options=["1", "2", "3", "4", "5", "6", "7", "8"])
    booking_date = st.date_input("التاريخ", date.today())
    
    submit = st.form_submit_button("تأكيد الحجز")

if submit:
    if teacher_name:
        conn = sqlite3.connect('school_booking_v2.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bookings WHERE location=? AND period=? AND booking_date=?', 
                       (location, period, str(booking_date)))
        if cursor.fetchone():
            st.error("❌ هذا المكان محجوز بالفعل في هذا الوقت!")
        else:
            cursor.execute('INSERT INTO bookings (teacher_name, location, grade, subject, period, booking_date) VALUES (?,?,?,?,?,?)',
                           (teacher_name, location, grade, subject, period, str(booking_date)))
            conn.commit()
            st.success("✅ تم الحجز بنجاح")
        conn.close()
    else:
        st.warning("⚠️ يرجى كتابة اسم المعلم")

st.markdown("---")

# --- 3. عرض الجدول وقسم الإدارة (تعديل/حذف) ---
st.header("📋 الحجوزات الحالية وإدارتها")

conn = sqlite3.connect('school_booking_v2.db')
df = pd.read_sql_query("SELECT * FROM bookings", conn)
conn.close()

if not df.empty:
    st.dataframe(df.drop(columns=['id']), use_container_width=True)
    
    # خيارات الإدارة
    st.subheader("🛠️ خيارات الإدارة")
    record_to_manage = st.selectbox("اختر رقم الحجز (الترتيب في الجدول)", df.index, format_func=lambda x: f"حجز المعلم: {df.iloc[x]['teacher_name']} - حصة {df.iloc[x]['period']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ حذف الحجز المختار", use_container_width=True):
            conn = sqlite3.connect('school_booking_v2.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM bookings WHERE id=?', (int(df.iloc[record_to_manage]['id']),))
            conn.commit()
            conn.close()
            st.rerun()

    with col2:
        st.info("لتعديل حجز: احذفه ثم أضفه مجدداً بالبيانات الصحيحة.")
else:
    st.info("لا توجد حجوزات مسجلة حالياً.")