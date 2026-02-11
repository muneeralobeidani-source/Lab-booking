import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('lab_system_v18.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_name TEXT, subject TEXT, grade TEXT, 
            period TEXT, booking_date TEXT, purpose TEXT, notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# إعدادات الصفحة
st.set_page_config(page_title="حجز المختبر", layout="wide")

# تنسيق CSS لتحسين المظهر والطباعة
st.markdown("""
    <style>
    @media print {
        .stButton, .stSidebar, .stRadio, .stForm, .stHeader, .no-print { display: none !important; }
        .main { width: 100% !important; }
    }
    .main { background-color: #f8f9fa; }
    .stButton>button { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# العنوان الجديد المطلوب
st.title("حجز المختبر")

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
            t_purpose = st.radio("الغرض", ["تجربة عملية", "عرض تعليمي"], horizontal=True)
        
        t_notes = st.text_area("ملاحظات إضافية (اختياري)")
        submit_btn = st.form_submit_button("تأكيد الحجز")

    if submit_btn and t_name:
        d_str = t_date.strftime('%Y-%m-%d')
        conn = sqlite3.connect('lab_system_v18.db')
        cursor = conn.cursor()
        cursor.execute('SELECT teacher_name FROM bookings WHERE period = ? AND booking_date = ?', (t_period, d_str))
        existing = cursor.fetchone()
        
        if existing:
            st.error(f"🚨 تعارض! المختبر محجوز مسبقاً في الحصة {t_period} للأستاذ/ة: {existing[0]}")
        else:
            cursor.execute('INSERT INTO bookings (teacher_name, subject, grade, period, booking_date, purpose, notes) VALUES (?,?,?,?,?,?,?)',
                           (t_name, t_subject, t_grade, t_period, d_str, t_purpose, t_notes))
            conn.commit()
            st.balloons()
            st.success("✅ تم تأكيد الحجز بنجاح")
        conn.close()

    st.markdown("---")
    st.subheader("📋 جدول الحجوزات الحالي")
    conn = sqlite3.connect('lab_system_v18.db')
    df = pd.read_sql_query("SELECT * FROM bookings", conn)
    conn.close()

    if not df.empty:
        df_ar = df.rename(columns={'teacher_name': 'المعلم', 'subject': 'المادة', 'grade': 'الصف', 'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'})
        edited_df = st.data_editor(df_ar, column_config={"id": None}, num_rows="dynamic", use_container_width=True, key="t_edit")
        if st.button("💾 حفظ التعديلات"):
            conn = sqlite3.connect('lab_system_v18.db')
            final_df = edited_df.rename(columns={'المعلم': 'teacher_name', 'المادة': 'subject', 'الصف': 'grade', 'الحصة': 'period', 'التاريخ': 'booking_date', 'الغرض': 'purpose', 'الملاحظات': 'notes'})
            final_df.to_sql('bookings', conn, if_exists='replace', index=False)
            conn.close()
            st.success("✅ تم التحديث")
            st.rerun()

# --- 4. واجهة فني المختبر ---
else:
    st.subheader("🛠️ لوحة تحكم فني المختبر")
    pwd = st.sidebar.text_input("كلمة المرور:", type="password")
    
    if pwd == "1234":
        conn = sqlite3.connect('lab_system_v18.db')
        df_admin = pd.read_sql_query("SELECT * FROM bookings", conn)
        conn.close()

        if not df_admin.empty:
            st.markdown("### 📄 التقارير والطباعة")
            col_w, col_p = st.columns(2)
            with col_w:
                df_for_word = df_admin.drop(columns=['id']).rename(columns={'teacher_name': 'المعلم', 'subject': 'المادة', 'grade': 'الصف', 'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'})
                html_table = df_for_word.to_html(index=False).replace('border="1"', 'border="1" style="direction:rtl; width:100%; border-collapse:collapse; text-align:right;"')
                word_data = f"<html><meta charset='utf-8'><body><h2 style='text-align:center;'>حجوزات المختبر</h2>{html_table}</body></html>"
                st.download_button("📝 تنزيل كملف Word", data=word_data, file_name=f"حجوزات_{date.today()}.doc")
            with col_p:
                if st.button("🖨️ طباعة الجدول فوراً / PDF"):
                    st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

            st.markdown("---")
            st.write("🔧 **صلاحية الإدارة (تعديل وحذف):**")
            df_admin_ar = df_admin.rename(columns={'teacher_name': 'المعلم', 'subject': 'المادة', 'grade': 'الصف', 'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'})
            admin_edited = st.data_editor(df_admin_ar, column_config={"id": None}, num_rows="dynamic", use_container_width=True, key="adm_edit")
            if st.button("💾 حفظ التعديلات الإدارية"):
                conn = sqlite3.connect('lab_system_v18.db')
                final_admin_df = admin_edited.rename(columns={'المعلم': 'teacher_name', 'المادة': 'subject', 'الصف': 'grade', 'الحصة': 'period', 'التاريخ': 'booking_date', 'الغرض': 'purpose', 'الملاحظات': 'notes'})
                final_admin_df.to_sql('bookings', conn, if_exists='replace', index=False)
                conn.close()
                st.success("✅ تم تحديث البيانات إدارياً بنجاح")
                st.rerun()
    else:
        st.warning("يرجى إدخال كلمة المرور.")
