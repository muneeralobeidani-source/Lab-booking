import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('lab_system_final_pro.db')
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

# كود تنسيق الطباعة (CSS)
st.markdown("""
    <style>
    @media print {
        .stButton, .stSidebar, .stRadio, .stForm, .stHeader, .no-print {
            display: none !important;
        }
        .main { width: 100% !important; }
        .stDataFrame { font-size: 12pt; direction: rtl; }
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🔬 نظام حجز المختبر - أ. منير")

# --- 2. القائمة الجانبية ---
st.sidebar.title("🔐 بوابة الوصول")
user_role = st.sidebar.radio("اختر نوع المستخدم:", ["واجهة المعلمين (حجز وتعديل)", "فني المختبر (إدارة وطباعة)"])

# --- 3. واجهة المعلمين (حجز + تعديل) ---
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
        
        t_notes = st.text_area("ملاحظات إضافية (اختياري)")
        submit_btn = st.form_submit_button("تأكيد الحجز")

    if submit_btn and t_name:
        d_str = t_date.strftime('%Y-%m-%d')
        conn = sqlite3.connect('lab_system_final_pro.db')
        cursor = conn.cursor()
        # فحص التعارض
        cursor.execute('SELECT teacher_name FROM bookings WHERE period = ? AND booking_date = ?', (t_period, d_str))
        existing = cursor.fetchone()
        
        if existing:
            st.error(f"🚨 عذراً.. المختبر محجوز في الحصة {t_period} للأستاذ/ة: {existing[0]}")
        else:
            cursor.execute('''INSERT INTO bookings (teacher_name, subject, grade, period, booking_date, purpose, notes) 
                              VALUES (?,?,?,?,?,?,?)''', (t_name, t_subject, t_grade, t_period, d_str, t_purpose, t_notes))
            conn.commit()
            st.success("✅ تم تأكيد الحجز بنجاح")
        conn.close()

    st.markdown("---")
    st.subheader("📋 جدول الحجوزات (تعديل الحجوزات متاح هنا)")
    
    conn = sqlite3.connect('lab_system_final_pro.db')
    df = pd.read_sql_query("SELECT * FROM bookings", conn)
    conn.close()

    if not df.empty:
        # تعريب العناوين للمعلم
        df_ar = df.rename(columns={
            'teacher_name': 'المعلم', 'subject': 'المادة', 'grade': 'الصف',
            'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'
        })
        
        st.write("💡 **للمعلم:** يمكنك تعديل بياناتك مباشرة في الجدول ثم اضغط 'حفظ التغييرات'")
        edited_df = st.data_editor(df_ar, column_config={"id": None}, num_rows="dynamic", use_container_width=True, key="teacher_editor")
        
        if st.button("💾 حفظ التغييرات (بصفتك معلم)"):
            conn = sqlite3.connect('lab_system_final_pro.db')
            final_df = edited_df.rename(columns={
                'المعلم': 'teacher_name', 'المادة': 'subject', 'الصف': 'grade',
                'الحصة': 'period', 'التاريخ': 'booking_date', 'الغرض': 'purpose', 'الملاحظات': 'notes'
            })
            final_df.to_sql('bookings', conn, if_exists='replace', index=False)
            conn.close()
            st.success("✅ تم تحديث الجدول بنجاح")
            st.rerun()
    else:
        st.info("لا توجد حجوزات مسجلة حالياً.")

# --- 4. واجهة فني المختبر (أ. منير) - الإدارة العليا والطباعة ---
else:
    st.subheader("🛠️ لوحة تحكم أ. منير (الإدارة والطباعة)")
    pwd = st.sidebar.text_input("أدخل كلمة المرور:", type="password")
    
    if pwd == "1234":
        st.success("مرحباً أ. منير. يمكنك الآن إدارة النظام وتصدير التقارير.")
        
        conn = sqlite3.connect('lab_system_final_pro.db')
        df_admin = pd.read_sql_query("SELECT * FROM bookings", conn)
        conn.close()

        if not df_admin.empty:
            # قسم الطباعة والتصدير للفني فقط
            st.markdown("### 🖨️ أدوات التصدير والطباعة")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("📄 حفظ كـ PDF / طباعة الجدول"):
                    st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
            with col_b:
                csv = df_admin.drop(columns=['id']).to_csv(index=False).encode('utf-8-sig')
                st.download_button("📂 تصدير لـ Excel", data=csv, file_name=f"تقرير_مختبر_{date.today()}.csv")

            st.markdown("---")
            st.write("📝 **صلاحية الإدارة العليا (تعديل/حذف):**")
            df_admin_ar = df_admin.rename(columns={
                'teacher_name': 'المعلم', 'subject': 'المادة', 'grade': 'الصف',
                'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'
            })
            
            admin_edit = st.data_editor(df_admin_ar, column_config={"id": None}, num_rows="dynamic", use_container_width=True, key="admin_editor")
            
            if st.button("💾 حفظ التعديلات الإدارية"):
                conn = sqlite3.connect('lab_system_final_pro.db')
                final_admin_df = admin_edit.rename(columns={
                    'المعلم': 'teacher_name', 'المادة': 'subject', 'الصف': 'grade',
                    'الحصة': 'period', 'التاريخ': 'booking_date', 'الغرض': 'purpose', 'الملاحظات': 'notes'
                })
                final_admin_df.to_sql('bookings', conn, if_exists='replace', index=False)
                conn.close()
                st.success("✅ تم تحديث البيانات إدارياً")
                st.rerun()
        else:
            st.info("لا توجد بيانات متاحة حالياً.")
    else:
        st.warning("هذه المنطقة مخصصة لفني المختبر فقط.")
