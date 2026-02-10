import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('lab_booking_v4_final.db') # تغيير اسم القاعدة لضمان التحديث
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

st.set_page_config(page_title="حجز المختبر - أ. منير", layout="centered")
st.title("🔬 نظام حجز المختبر - أ. منير")

# --- 2. واجهة المعلم ---
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
        # تحويل التاريخ لنص واضح للمقارنة
        selected_date = str(t_date)
        
        conn = sqlite3.connect('lab_booking_v4_final.db')
        cursor = conn.cursor()
        
        # البحث عن أي حجز في نفس الحصة والتاريخ (تنظيف البيانات لضمان المطابقة)
        cursor.execute('SELECT teacher_name FROM bookings WHERE period = ? AND booking_date = ?', (t_period, selected_date))
        existing_booking = cursor.fetchone()
        
        if existing_booking:
            # رسالة تحذير قوية جداً تظهر في حالة التعارض
            st.warning(f"🚨 تنبيه تعارض: المختبر محجوز مسبقاً في الحصة ({t_period}) بتاريخ ({selected_date}) من قبل الأستاذ/ة: {existing_booking[0]}")
            st.error("❌ لم يتم الحجز. يرجى اختيار موعد آخر.")
        else:
            cursor.execute('''INSERT INTO bookings (teacher_name, subject, grade, period, booking_date, purpose) 
                              VALUES (?, ?, ?, ?, ?, ?)''', (t_name, t_subject, t_grade, t_period, selected_date, t_purpose))
            conn.commit()
            st.balloons() # بالونات احتفال عند النجاح
            st.success(f"✅ تم تأكيد حجزك بنجاح أستاذ {t_name}")
        conn.close()
        # ملاحظة: تم إزالة st.rerun() هنا للسماح للرسالة بالبقاء ظاهرة
    else:
        st.error("⚠️ يرجى كتابة اسمك أولاً")

st.markdown("---")

# --- 3. عرض الجدول والإدارة ---
st.subheader("📋 جدول الحجوزات (تعديل وحذف)")
conn = sqlite3.connect('lab_booking_v4_final.db')
df = pd.read_sql_query("SELECT * FROM bookings", conn)
conn.close()

if not df.empty:
    edited_df = st.data_editor(
        df,
        column_config={"id": None},
        num_rows="dynamic",
        use_container_width=True,
        key="main_editor"
    )

    if st.button("💾 حفظ التعديلات"):
        conn = sqlite3.connect('lab_booking_v4_final.db')
        edited_df.to_sql('bookings', conn, if_exists='replace', index=False)
        conn.close()
        st.success("✅ تم التحديث")
        st.rerun()
else:
    st.info("لا توجد حجوزات مسجلة.")
