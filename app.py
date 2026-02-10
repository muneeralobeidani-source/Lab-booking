import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('lab_booking_system_v3.db')
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
st.set_page_config(page_title="حجز المختبر - أ. منير", layout="centered")
st.title("🔬 نظام حجز المختبر - أ. منير")

# --- 2. واجهة المعلم (إضافة حجز مع نظام منع التعارض) ---
st.subheader("📝 تسجيل حجز جديد")
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
        conn = sqlite3.connect('lab_booking_system_v3.db')
        cursor = conn.cursor()
        
        # هـنـا كود فحص التعارض (نفس التاريخ والحصة)
        cursor.execute('SELECT teacher_name FROM bookings WHERE period=? AND booking_date=?', (t_period, str(t_date)))
        existing_booking = cursor.fetchone()
        
        if existing_booking:
            # رسالة التنبيه في حالة التعارض
            st.error(f"⚠️ تعارض في الحجز! المختبر محجوز مسبقاً في الحصة {t_period} من قبل الأستاذ/ة: ({existing_booking[0]}). يرجى اختيار حصة أو تاريخ آخر.")
        else:
            # إذا لم يوجد تعارض، يتم الحجز
            cursor.execute('''INSERT INTO bookings (teacher_name, subject, grade, period, booking_date, purpose) 
                              VALUES (?, ?, ?, ?, ?, ?)''', (t_name, t_subject, t_grade, t_period, str(t_date), t_purpose))
            conn.commit()
            st.success(f"✅ تم تأكيد حجزك بنجاح أستاذ {t_name}")
        conn.close()
        st.rerun()
    else:
        st.warning("⚠️ يرجى إدخال اسم المعلم أولاً")

st.markdown("---")

# --- 3. واجهة الإدارة والتعديل والحذف ---
st.subheader("📋 جدول الحجوزات (تعديل وحذف)")
conn = sqlite3.connect('lab_booking_system_v3.db')
df = pd.read_sql_query("SELECT * FROM bookings", conn)
conn.close()

if not df.empty:
    st.write("💡 يمكنك التعديل مباشرة في الجدول أدناه، أو تحديد صف وحذفه ثم الضغط على حفظ.")
    
    edited_df = st.data_editor(
        df,
        column_config={"id": None}, # إخفاء عمود ID
        num_rows="dynamic", # يتيح حذف الصفوف
        use_container_width=True,
        key="main_editor"
    )

    if st.button("💾 حفظ التعديلات النهائية (تعديل/حذف)"):
        conn = sqlite3.connect('lab_booking_system_v3.db')
        edited_df.to_sql('bookings', conn, if_exists='replace', index=False)
        conn.close()
        st.success("✅ تم تحديث البيانات بنجاح")
        st.rerun()
else:
    st.info("لا توجد حجوزات مسجلة حالياً.")
