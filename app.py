import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('lab_booking_system.db')
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

# إعدادات واجهة التطبيق
st.set_page_config(page_title="حجز المختبر - أ. منير", layout="centered")
st.title("🔬 نظام حجز المختبر - أ. منير")

# --- 2. القائمة الجانبية للتنقل ---
st.sidebar.header("بوابة الدخول")
user_role = st.sidebar.radio("اختر نوع المستخدم:", ["معلم (حجز ورؤية)", "فني المختبر (إدارة كاملة)"])

# --- 3. واجهة المعلمين (إضافة ورؤية فقط) ---
if user_role == "معلم (حجز ورؤية)":
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
            conn = sqlite3.connect('lab_booking_system.db')
            cursor = conn.cursor()
            # فحص التعارض (منع الحجز في نفس الحصة والتاريخ)
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
            st.warning("⚠️ يرجى إدخال اسم المعلم أولاً")

    st.markdown("---")
    st.subheader("📅 جدول الحجوزات الحالي")
    conn = sqlite3.connect('lab_booking_system.db')
    display_df = pd.read_sql_query("SELECT teacher_name as 'المعلم', subject as 'المادة', grade as 'الصف', period as 'الحصة', booking_date as 'التاريخ', purpose as 'الغرض' FROM bookings", conn)
    st.table(display_df)
    conn.close()

# --- 4. واجهة فني المختبر (أ. منير) ---
else:
    st.subheader("🔐 لوحة تحكم فني المختبر")
    admin_pass = st.sidebar.text_input("كلمة مرور الفني:", type="password")
    
    if admin_pass == "1234": # يمكنك تغيير كلمة المرور هنا
        st.info("مرحباً أ. منير، يمكنك الآن تعديل أو حذف أي حجز من الجدول مباشرة.")
        
        conn = sqlite3.connect('lab_booking_system.db')
        df = pd.read_sql_query("SELECT * FROM bookings", conn)
        
        if not df.empty:
            # جدول تفاعلي للإدارة
            edited_df = st.data_editor(
                df,
                column_config={"id": None}, # إخفاء معرف قاعدة البيانات
                num_rows="dynamic", 
                use_container_width=True,
                key="admin_editor"
            )
            
            if st.button("💾 حفظ التعديلات أو الحذف النهائي"):
                # تحديث قاعدة البيانات بناءً على التعديلات
                edited_df.to_sql('bookings', conn, if_exists='replace', index=False)
                st.success("✅ تم تحديث وإدارة الحجوزات بنجاح")
                st.rerun()
        else:
            st.info("لا توجد حجوزات مسجلة حالياً.")
        conn.close()
    else:
        st.error("يرجى إدخال كلمة المرور الصحيحة للوصول لصلاحيات الإدارة.")
