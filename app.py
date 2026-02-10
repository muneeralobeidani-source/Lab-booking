import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('lab_booking_system_final_v6.db')
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

# --- 2. القائمة الجانبية (Sidebar) ---
st.sidebar.title("🔐 بوابة الوصول")
user_role = st.sidebar.radio("اختر نوع المستخدم:", ["واجهة المعلمين (حجز وإدارة)", "فني المختبر (إدارة عليا)"])

# --- 3. واجهة المعلمين (حجز + تعديل + حذف) ---
if user_role == "واجهة المعلمين (حجز وإدارة)":
    st.subheader("📝 تسجيل حجز جديد")
    with st.form("booking_form", clear_on_submit=True):
        t_name = st.text_input("اسم المعلم")
        t_subject = st.selectbox("المادة", ["علوم", "فيزياء", "كيمياء", "أحياء", "علوم وبيئة", "آخر"])
        t_grade = st.selectbox("الصف", [str(i) for i in range(1, 13)])
        t_period = st.selectbox("الحصة", [str(i) for i in range(1, 9)])
        t_date = st.date_input("التاريخ", date.today())
        t_purpose = st.radio("الغرض", ["تجربة عملية", "عرض تعليمي"])
        submit_btn = st.form_submit_button("تأكيد الحجز")

    if submit_btn and t_name:
        conn = sqlite3.connect('lab_booking_system_final_v6.db')
        cursor = conn.cursor()
        # كود منع التعارض
        cursor.execute('SELECT teacher_name FROM bookings WHERE period = ? AND booking_date = ?', (t_period, str(t_date)))
        existing = cursor.fetchone()
        
        if existing:
            st.error(f"🚨 تعارض! المختبر محجوز مسبقاً في الحصة {t_period} للأستاذ/ة: {existing[0]}")
        else:
            cursor.execute('INSERT INTO bookings (teacher_name, subject, grade, period, booking_date, purpose) VALUES (?,?,?,?,?,?)',
                           (t_name, t_subject, t_grade, t_period, str(t_date), t_purpose))
            conn.commit()
            st.success("✅ تم تأكيد الحجز بنجاح")
        conn.close()
        st.rerun()

    st.markdown("---")
    st.subheader("📋 جدول الحجوزات (متاح للمعلمين للتعديل والحذف)")
    conn = sqlite3.connect('lab_booking_system_final_v6.db')
    df = pd.read_sql_query("SELECT * FROM bookings", conn)
    conn.close()

    if not df.empty:
        # المعلم يمكنه التعديل والحذف هنا
        edited_df = st.data_editor(df, column_config={"id": None}, num_rows="dynamic", use_container_width=True, key="teacher_view")
        if st.button("💾 حفظ التغييرات (للمعلمين)"):
            conn = sqlite3.connect('lab_booking_system_final_v6.db')
            edited_df.to_sql('bookings', conn, if_exists='replace', index=False)
            conn.close()
            st.success("✅ تم تحديث الجدول")
            st.rerun()
    else:
        st.info("لا توجد حجوزات حالياً.")

# --- 4. واجهة فني المختبر (أ. منير) - الإدارة العليا ---
else:
    st.subheader("🛠️ لوحة الإدارة العليا - أ. منير")
    password = st.sidebar.text_input("أدخل كلمة المرور:", type="password")
    
    if password == "1234":
        st.success("مرحباً أ. منير. هذه اللوحة لمراقبة وإدارة جميع العمليات.")
        conn = sqlite3.connect('lab_booking_system_final_v6.db')
        df_admin = pd.read_sql_query("SELECT * FROM bookings", conn)
        
        if not df_admin.empty:
            # الفني يرى عمود الـ ID أيضاً للرقابة الدقيقة
            admin_edit = st.data_editor(df_admin, num_rows="dynamic", use_container_width=True, key="admin_view")
            if st.button("💾 حفظ التعديلات الإدارية"):
                admin_edit.to_sql('bookings', conn, if_exists='replace', index=False)
                conn.close()
                st.success("✅ تم التحديث الإداري بنجاح")
                st.rerun()
        else:
            st.info("المستودع فارغ حالياً.")
    else:
        st.warning("هذه المنطقة مخصصة لفني المختبر فقط.")
