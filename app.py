import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('lab_pro_final_v15.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_name TEXT, 
            subject TEXT, 
            grade TEXT, 
            period TEXT, 
            booking_date TEXT, 
            purpose TEXT,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

st.set_page_config(page_title="حجز المختبر - أ. منير", layout="wide")

st.title("🔬 نظام حجز المختبر - أ. منير")

# --- 2. القائمة الجانبية ---
st.sidebar.title("🔐 بوابة الوصول")
user_role = st.sidebar.radio("اختر نوع المستخدم:", ["واجهة المعلمين (حجز وتعديل)", "فني المختبر (إدارة وطباعة)"])

# --- 3. واجهة المعلمين ---
if user_role == "واجهة المعلمين (حجز وتعديل)":
    st.subheader("📝 تسجيل حجز جديد")
    with st.form("booking_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            t_name = st.text_input("اسم المعلم")
            t_subject = st.selectbox("المادة", ["علوم", "فيزياء", "كيمياء", "أحياء", "علوم وبيئة", "آخر"])
            t_grade = st.selectbox("الصف", [str(i) for i in range(1, 13)])
        with col2:
            t_period = st.selectbox("الحصة", [str(i) for i in range(1, 9)])
            t_date = st.date_input("التاريخ", date.today())
            t_purpose = st.radio("الغرض", ["تجربة عملية", "عرض تعليمي"])
        
        t_notes = st.text_area("ملاحظات إضافية")
        submit_btn = st.form_submit_button("تأكيد الحجز")

    if submit_btn and t_name:
        d_str = t_date.strftime('%Y-%m-%d')
        conn = sqlite3.connect('lab_pro_final_v15.db')
        cursor = conn.cursor()
        cursor.execute('SELECT teacher_name FROM bookings WHERE period = ? AND booking_date = ?', (t_period, d_str))
        existing = cursor.fetchone()
        
        if existing:
            st.error(f"🚨 تعارض! المختبر محجوز للأستاذ/ة: {existing[0]}")
        else:
            cursor.execute('INSERT INTO bookings (teacher_name, subject, grade, period, booking_date, purpose, notes) VALUES (?,?,?,?,?,?,?)',
                           (t_name, t_subject, t_grade, t_period, d_str, t_purpose, t_notes))
            conn.commit()
            st.success("✅ تم تأكيد الحجز بنجاح")
        conn.close()

    st.markdown("---")
    st.subheader("📋 جدول الحجوزات الحالي")
    conn = sqlite3.connect('lab_pro_final_v15.db')
    df = pd.read_sql_query("SELECT * FROM bookings", conn)
    conn.close()

    if not df.empty:
        df_ar = df.rename(columns={'teacher_name': 'المعلم', 'subject': 'المادة', 'grade': 'الصف', 'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'})
        edited_df = st.data_editor(df_ar, column_config={"id": None}, num_rows="dynamic", use_container_width=True)
        if st.button("💾 حفظ التعديلات"):
            conn = sqlite3.connect('lab_pro_final_v15.db')
            final_df = edited_df.rename(columns={'المعلم': 'teacher_name', 'المادة': 'subject', 'الصف': 'grade', 'الحصة': 'period', 'التاريخ': 'booking_date', 'الغرض': 'purpose', 'الملاحظات': 'notes'})
            final_df.to_sql('bookings', conn, if_exists='replace', index=False)
            conn.close()
            st.success("✅ تم التحديث")
            st.rerun()

# --- 4. واجهة فني المختبر (أ. منير) - تصدير Word ---
else:
    st.subheader("🛠️ لوحة الإدارة - أ. منير")
    pwd = st.sidebar.text_input("كلمة المرور:", type="password")
    
    if pwd == "1234":
        conn = sqlite3.connect('lab_pro_final_v15.db')
        df_admin = pd.read_sql_query("SELECT teacher_name, subject, grade, period, booking_date, purpose, notes FROM bookings", conn)
        conn.close()

        if not df_admin.empty:
            df_admin.columns = ['المعلم', 'المادة', 'الصف', 'الحصة', 'التاريخ', 'الغرض', 'الملاحظات']
            
            st.markdown("### 📄 خيارات الطباعة المتقدمة")
            
            # زر التصدير لملف Word
            # نقوم بتحويل الجدول لـ HTML بتنسيق يدعمه Word
            html = df_admin.to_html(index=False).replace('border="1"', 'border="1" style="direction:rtl; border-collapse:collapse; width:100%; text-align:right;"')
            word_html = f"<html><meta charset='utf-8'><body><h2 style='text-align:center;'>جدول حجوزات المختبر</h2>{html}</body></html>"
            
            st.download_button(
                label="📝 تنزيل الجدول لفتحه في برنامج Word",
                data=word_html,
                file_name=f"حجوزات_المختبر_{date.today()}.doc",
                mime="application/msword"
            )

            if st.button("🖨️ طباعة فورية / PDF"):
                st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
            
            st.table(df_admin)
        else:
            st.info("لا توجد بيانات للطباعة.")
