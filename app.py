import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('school_booking_final.db')
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

st.set_page_config(page_title="نظام حجز المرافق", layout="centered")

# --- واجهة الإضافة ---
st.title("🏫 نظام حجز المختبرات والصفوف")

with st.expander("➕ إضافة حجز جديد", expanded=True):
    with st.form("booking_form", clear_on_submit=True):
        teacher_name = st.text_input("اسم المعلم")
        
        col1, col2 = st.columns(2)
        with col1:
            location = st.selectbox("المكان", ["مختبر العلوم", "الصف الدراسي", "قاعة الحاسوب"])
            # تم تغييرها من منزلق إلى قائمة عادية كما طلبت
            grade = st.selectbox("الصف", [str(i) for i in range(5, 13)])
        
        with col2:
            subject = st.selectbox("المادة", ["علوم", "فيزياء", "كيمياء", "أحياء", "علوم وبيئة"])
            # تم تغييرها من منزلق إلى قائمة عادية كما طلبت
            period = st.selectbox("الحصة", [str(i) for i in range(1, 9)])
            
        booking_date = st.date_input("التاريخ", date.today())
        
        submit_btn = st.form_submit_button("تأكيد الحجز")

if submit_btn and teacher_name:
    conn = sqlite3.connect('school_booking_final.db')
    cursor = conn.cursor()
    # التحقق من التعارض
    cursor.execute('SELECT * FROM bookings WHERE location=? AND period=? AND booking_date=?', 
                   (location, period, str(booking_date)))
    if cursor.fetchone():
        st.error(f"❌ عذراً، {location} محجوز بالفعل في الحصة {period}!")
    else:
        cursor.execute('''INSERT INTO bookings (teacher_name, location, grade, subject, period, booking_date) 
                          VALUES (?, ?, ?, ?, ?, ?)''', 
                       (teacher_name, location, grade, subject, period, str(booking_date)))
        conn.commit()
        st.success(f"✅ تم تسجيل حجز الأستاذ/ة {teacher_name}")
    conn.close()
    st.rerun()

st.markdown("---")

# --- واجهة العرض والحذف والتعديل ---
st.header("📋 جدول الحجوزات")

conn = sqlite3.connect('school_booking_final.db')
df = pd.read_sql_query("SELECT * FROM bookings", conn)
conn.close()

if not df.empty:
    st.write("🗑️ **للحذف:** اختر الصف الذي تريد حذفه ثم اضغط على زر الحذف في الجدول أو استخدم زر الحفظ أدناه.")
    
    # الجدول التفاعلي الذي يتيح لك الحذف والتعديل باللمس
    edited_df = st.data_editor(
        df,
        column_config={
            "id": None, # إخفاء معرف قاعدة البيانات
            "teacher_name": "المعلم",
            "location": "المكان",
            "grade": "الصف",
            "subject": "المادة",
            "period": "الحصة",
            "booking_date": "التاريخ"
        },
        num_rows="dynamic", # يتيح لك حذف الصفوف يدوياً
        use_container_width=True,
        key="editor"
    )

    # حفظ التغييرات بعد الحذف أو التعديل
    if st.button("💾 حفظ التعديلات أو الحذف"):
        conn = sqlite3.connect('school_booking_final.db')
        # إعادة حفظ البيانات المعدلة (التي قد ينقص منها صفوف محذوفة)
        edited_df.to_sql('bookings', conn, if_exists='replace', index=False)
        conn.close()
        st.success("✅ تم تحديث الجدول بنجاح!")
        st.rerun()
else:
    st.info("لا توجد حجوزات مسجلة حالياً.")
