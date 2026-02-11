import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('lab_booking_v9.db')
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

st.set_page_config(page_title="حجز المختبر - أ. منير", layout="centered")
st.title("🔬 نظام حجز المختبر - أ. منير")

# --- 2. القائمة الجانبية ---
st.sidebar.title("🔐 بوابة الوصول")
user_role = st.sidebar.radio("اختر نوع المستخدم:", ["واجهة المعلمين", "فني المختبر (أ. منير)"])

# --- 3. واجهة المعلمين ---
if user_role == "واجهة المعلمين":
    st.subheader("📝 تسجيل حجز جديد")
    with st.form("booking_form", clear_on_submit=True):
        t_name = st.text_input("اسم المعلم")
        t_subject = st.selectbox("المادة", ["علوم", "فيزياء", "كيمياء", "أحياء", "علوم وبيئة", "آخر"])
        t_grade = st.selectbox("الصف", [str(i) for i in range(1, 13)])
        t_period = st.selectbox("الحصة", [str(i) for i in range(1, 9)])
        t_date = st.date_input("التاريخ", date.today())
        t_purpose = st.radio("الغرض", ["تجربة عملية", "عرض تعليمي"])
        t_notes = st.text_area("ملاحظات إضافية (اختياري)")
        
        submit_btn = st.form_submit_button("تأكيد الحجز")

    if submit_btn:
        if t_name:
            d_str = t_date.strftime('%Y-%m-%d')
            conn = sqlite3.connect('lab_booking_v9.db')
            cursor = conn.cursor()
            cursor.execute('SELECT teacher_name FROM bookings WHERE period = ? AND booking_date = ?', (t_period, d_str))
            existing = cursor.fetchone()
            
            if existing:
                st.error(f"🚨 عذراً أستاذ {t_name}.. المختبر محجوز مسبقاً في الحصة ({t_period}) بتاريخ ({d_str}) من قبل الأستاذ/ة: {existing[0]}")
            else:
                cursor.execute('''INSERT INTO bookings (teacher_name, subject, grade, period, booking_date, purpose, notes) 
                                  VALUES (?, ?, ?, ?, ?, ?, ?)''', (t_name, t_subject, t_grade, t_period, d_str, t_purpose, t_notes))
                conn.commit()
                st.success(f"✅ تم تأكيد حجزك بنجاح")
            conn.close()
        else:
            st.warning("⚠️ يرجى كتابة اسم المعلم")

    st.markdown("---")
    st.subheader("📋 جدول الحجوزات الحالي")
    
    conn = sqlite3.connect('lab_booking_v9.db')
    df = pd.read_sql_query("SELECT id, teacher_name, subject, grade, period, booking_date, purpose, notes FROM bookings", conn)
    conn.close()

    df_ar = df.rename(columns={
        'teacher_name': 'اسم المعلم', 'subject': 'المادة', 'grade': 'الصف',
        'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'
    })

    if not df_ar.empty:
        # خيار تحميل الجدول للطباعة
        csv = df_ar.drop(columns=['id']).to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 تحميل الجدول للطباعة (Excel/CSV)",
            data=csv,
            file_name=f'حجوزات_المختبر_{date.today()}.csv',
            mime='text/csv',
        )
        
        st.write("💡 يمكنك التعديل أو الحذف من الجدول ثم الحفظ:")
        edited_df = st.data_editor(df_ar, column_config={"id": None}, num_rows="dynamic", use_container_width=True)
        
        if st.button("💾 حفظ التغييرات"):
            conn = sqlite3.connect('lab_booking_v9.db')
            final_df = edited_df.rename(columns={
                'اسم المعلم': 'teacher_name', 'المادة': 'subject', 'الصف': 'grade',
                'الحصة': 'period', 'التاريخ': 'booking_date', 'الغرض': 'purpose', 'الملاحظات': 'notes'
            })
            final_df.to_sql('bookings', conn, if_exists='replace', index=False)
            conn.close()
            st.success("✅ تم تحديث الجدول")
            st.rerun()
    else:
        st.info("لا توجد حجوزات مسجلة.")

# --- 4. واجهة فني المختبر ---
else:
    st.subheader("🛠️ الإدارة العليا - أ. منير")
    pwd = st.sidebar.text_input("كلمة المرور:", type="password")
    if pwd == "1234":
        st.success("مرحباً أ. منير")
        conn = sqlite3.connect('lab_booking_v9.db')
        df_admin = pd.read_sql_query("SELECT * FROM bookings", conn)
        st.dataframe(df_admin, use_container_width=True)
        conn.close()
    else:
        st.warning("الوصول مقتصر على فني المختبر.")
