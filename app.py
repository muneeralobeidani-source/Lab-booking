import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('lab_booking_final_v2.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_name TEXT, 
            subject TEXT, 
            grade TEXT, 
            period TEXT, 
            booking_date TEXT, 
            purpose TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# إعدادات الصفحة
st.set_page_config(page_title="نظام حجز المختبر - أ. منير", layout="centered")
st.title("🔬 نظام حجز المختبر - أ. منير")

# --- 2. قسم إضافة حجز جديد (مع منع التعارض) ---
st.subheader("📝 تسجيل طلب حجز جديد")
with st.form("booking_form", clear_on_submit=True):
    t_name = st.text_input("اسم المعلم")
    t_subject = st.selectbox("المادة", ["علوم", "فيزياء", "كيمياء", "أحياء", "علوم وبيئة", "آخر"])
    t_grade = st.selectbox("الصف", [str(i) for i in range(1, 13)])
    t_period = st.selectbox("الحصة", [str(i) for i in range(1, 9)])
    t_date = st.date_input("التاريخ", date.today())
    t_purpose = st.radio("الغرض من الحجز", ["تجربة عملية", "عرض تعليمي"])
    
    submit_btn = st.form_submit_button("تأكيد الحجز")

if submit_btn:
    if t_name:
        conn = sqlite3.connect('lab_booking_final_v2.db')
        cursor = conn.cursor()
        # فحص التعارض: منع الحجز في نفس التاريخ والحصة
        cursor.execute('SELECT * FROM bookings WHERE period=? AND booking_date=?', (t_period, str(t_date)))
        if cursor.fetchone():
            st.error(f"⚠️ عذراً، المختبر محجوز بالفعل في الحصة {t_period} بتاريخ {t_date}")
        else:
            cursor.execute('''INSERT INTO bookings (teacher_name, subject, grade, period, booking_date, purpose) 
                              VALUES (?, ?, ?, ?, ?, ?)''', (t_name, t_subject, t_grade, t_period, str(t_date), t_purpose))
            conn.commit()
            st.success(f"✅ تم تسجيل حجزك بنجاح أستاذ {t_name}")
        conn.close()
        st.rerun()
    else:
        st.warning("⚠️ يرجى إدخال اسم المعلم")

st.markdown("---")

# --- 3. قسم عرض وإدارة الحجوزات (متاح للجميع) ---
st.subheader("📋 إدارة وتعديل الحجوزات")

conn = sqlite3.connect('lab_booking_final_v2.db')
df = pd.read_sql_query("SELECT * FROM bookings", conn)
conn.close()

if not df.empty:
    st.write("💡 يمكن للمعلم التعديل مباشرة في الجدول أو اختيار صف لحذفه:")
    
    # جدول تفاعلي يسمح للمعلم بالتعديل والحذف مباشرة
    edited_df = st.data_editor(
        df,
        column_config={
            "id": None, # إخفاء عمود المعرف الداخلي
            "teacher_name": "اسم المعلم",
            "subject": "المادة",
            "grade": "الصف",
            "period": "الحصة",
            "booking_date": "التاريخ",
            "purpose": "الغرض"
        },
        num_rows="dynamic", # يسمح بحذف الصفوف بالضغط عليها
        use_container_width=True,
        key="teacher_editor"
    )

    if st.button("💾 حفظ التعديلات أو الحذف النهائي"):
        conn = sqlite3.connect('lab_booking_final_v2.db')
        # تحديث قاعدة البيانات بناءً على الجدول المعدل
        edited_df.to_sql('bookings', conn, if_exists='replace', index=False)
        conn.close()
        st.success("✅ تم تحديث الجدول بنجاح!")
        st.rerun()
else:
    st.info("لا توجد حجوزات مسجلة حالياً.")
