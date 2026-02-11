import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('lab_booking_v12.db')
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

# كود CSS لتحسين مظهر الطباعة
st.markdown("""
    <style>
    @media print {
        .stButton, .stSidebar, .stRadio, .stForm, .stHeader, .instructions {
            display: none !important;
        }
        .main { width: 100% !important; }
        table { direction: rtl; width: 100%; border-collapse: collapse; }
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🔬 نظام حجز المختبر - أ. منير")

# --- 2. القائمة الجانبية ---
st.sidebar.title("🔐 بوابة الوصول")
user_role = st.sidebar.radio("اختر نوع المستخدم:", ["واجهة المعلمين (حجز وتعديل)", "فني المختبر (طباعة وتقارير)"])

# --- 3. واجهة المعلمين (حجز + تعديل متاح للجميع) ---
if user_role == "واجهة المعلمين (حجز وتعديل)":
    st.subheader("📝 تسجيل حجز جديد")
    with st.form("booking_form", clear_on_submit=True):
        t_name = st.text_input("اسم المعلم")
        t_subject = st.selectbox("المادة", ["علوم", "فيزياء", "كيمياء", "أحياء", "علوم وبيئة", "آخر"])
        t_grade = st.selectbox("الصف", [str(i) for i in range(1, 13)])
        t_period = st.selectbox("الحصة", [str(i) for i in range(1, 9)])
        t_date = st.date_input("التاريخ", date.today())
        t_purpose = st.radio("الغرض", ["تجربة عملية", "عرض تعليمي"])
        t_notes = st.text_area("ملاحظات إضافية")
        submit_btn = st.form_submit_button("تأكيد الحجز")

    if submit_btn and t_name:
        d_str = t_date.strftime('%Y-%m-%d')
        conn = sqlite3.connect('lab_booking_v12.db')
        cursor = conn.cursor()
        cursor.execute('SELECT teacher_name FROM bookings WHERE period = ? AND booking_date = ?', (t_period, d_str))
        existing = cursor.fetchone()
        
        if existing:
            st.error(f"🚨 تعارض! المختبر محجوز للأستاذ/ة: {existing[0]}")
        else:
            cursor.execute('INSERT INTO bookings (teacher_name, subject, grade, period, booking_date, purpose, notes) VALUES (?,?,?,?,?,?,?)',
                           (t_name, t_subject, t_grade, t_period, d_str, t_purpose, t_notes))
            conn.commit()
            st.success("✅ تم تأكيد الحجز")
        conn.close()

    st.markdown("---")
    st.subheader("📋 جدول الحجوزات (يمكنك التعديل هنا)")
    
    conn = sqlite3.connect('lab_booking_v12.db')
    df = pd.read_sql_query("SELECT id, teacher_name, subject, grade, period, booking_date, purpose, notes FROM bookings", conn)
    conn.close()

    if not df.empty:
        df_ar = df.rename(columns={
            'teacher_name': 'اسم المعلم', 'subject': 'المادة', 'grade': 'الصف',
            'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'
        })
        
        # المعلم يستطيع التعديل والحذف هنا مباشرة
        st.markdown('<p class="instructions">💡 عدل البيانات في الجدول ثم اضغط "حفظ التغييرات":</p>', unsafe_allow_html=True)
        edited_df = st.data_editor(df_ar, column_config={"id": None}, num_rows="dynamic", use_container_width=True)
        
        if st.button("💾 حفظ التغييرات (للمعلم)"):
            conn = sqlite3.connect('lab_booking_v12.db')
            final_df = edited_df.rename(columns={
                'اسم المعلم': 'teacher_name', 'المادة': 'subject', 'الصف': 'grade',
                'الحصة': 'period', 'التاريخ': 'booking_date', 'الغرض': 'purpose', 'الملاحظات': 'notes'
            })
            final_df.to_sql('bookings', conn, if_exists='replace', index=False)
            conn.close()
            st.success("✅ تم تحديث بياناتك بنجاح")
            st.rerun()
    else:
        st.info("لا توجد حجوزات.")

# --- 4. واجهة فني المختبر (الطباعة والتقارير فقط) ---
else:
    st.subheader("🛠️ الإدارة والطباعة - أ. منير")
    pwd = st.sidebar.text_input("كلمة المرور:", type="password")
    
    if pwd == "1234":
        st.success("مرحباً أ. منير. هذه المنطقة مخصصة لاستخراج التقارير.")
        conn = sqlite3.connect('lab_booking_v12.db')
        df_admin = pd.read_sql_query("SELECT teacher_name, subject, grade, period, booking_date, purpose, notes FROM bookings", conn)
        conn.close()

        if not df_admin.empty:
            df_admin.columns = ['اسم المعلم', 'المادة', 'الصف', 'الحصة', 'التاريخ', 'الغرض', 'الملاحظات']
            
            st.markdown("### 🖨️ أدوات الطباعة")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🖨️ طباعة الجدول / حفظ PDF"):
                    st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
            with col2:
                csv = df_admin.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 تحميل Excel", data=csv, file_name=f"تقرير_المختبر_{date.today()}.csv")
            
            st.table(df_admin) # عرض الجدول للفني كشكل نهائي للطباعة
        else:
            st.info("لا توجد بيانات للطباعة.")
    else:
        st.warning("يرجى إدخال كلمة المرور للوصول لأدوات الطباعة.")
