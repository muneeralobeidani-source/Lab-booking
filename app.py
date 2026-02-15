import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('lab_identity_v20.db')
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
st.set_page_config(page_title="نظام حجز المختبر", layout="wide")

# --- لمسة الهوية البصرية (CSS المتقدم) ---
st.markdown("""
    <style>
    /* تغيير الخلفية العامة */
    .stApp {
        background: linear-gradient(to bottom, #f0f2f5, #ffffff);
    }
    
    /* تنسيق العنوان الرئيسي */
    .main-title {
        color: #1e3a8a;
        text-align: center;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: bold;
        padding: 20px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 30px;
    }
    
    /* تنسيق الحاويات (Cards) */
    .custom-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid #e5e7eb;
        margin-bottom: 20px;
    }

    /* تنسيق الأزرار */
    .stButton>button {
        background-color: #1e3a8a;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    /* تنسيق خاص لزر الوورد */
    div.stDownloadButton > button {
        background-color: #10b981 !important;
        color: white !important;
        border-radius: 10px !important;
    }

    /* إخفاء العناصر عند الطباعة */
    @media print {
        .stButton, .stSidebar, .stRadio, .stForm, .stHeader { display: none !important; }
        .main { width: 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# عرض العنوان بالهوية الجديدة
st.markdown('<div class="main-title">📑 نظام حجز المختبر الموحد</div>', unsafe_allow_html=True)

# --- 2. القائمة الجانبية ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>👤 الدخول</h2>", unsafe_allow_html=True)
    user_role = st.radio("اختر الواجهة:", ["بوابة المعلمين", "لوحة التحكم (أ. منير)"])
    st.markdown("---")
    st.info("نظام إلكتروني لتنظيم حجوزات المختبر المدرسي لضمان أعلى كفاءة.")

# --- 3. واجهة المعلمين ---
if user_role == "بوابة المعلمين":
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("📝 طلب حجز جديد")
    with st.form("booking_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            t_name = st.text_input("👤 اسم المعلم")
            t_subject = st.selectbox("📚 المادة", ["علوم", "فيزياء", "كيمياء", "أحياء", "علوم وبيئة", "آخر"])
            t_grade = st.selectbox("🏫 الصف", [str(i) for i in range(1, 13)])
        with c2:
            t_period = st.selectbox("⏰ الحصة", [str(i) for i in range(1, 9)])
            t_date = st.date_input("📅 التاريخ", date.today())
            t_purpose = st.radio("🎯 الغرض", ["تجربة عملية", "عرض تعليمي"], horizontal=True)
        
        t_notes = st.text_area("🗒️ ملاحظات إضافية (اختياري)")
        submit_btn = st.form_submit_button("تأكيد وإرسال الحجز")
    st.markdown('</div>', unsafe_allow_html=True)

    if submit_btn and t_name:
        d_str = t_date.strftime('%Y-%m-%d')
        conn = sqlite3.connect('lab_identity_v20.db')
        cursor = conn.cursor()
        cursor.execute('SELECT teacher_name FROM bookings WHERE period = ? AND booking_date = ?', (t_period, d_str))
        existing = cursor.fetchone()
        
        if existing:
            st.error(f"🚨 عذراً، المختبر محجوز مسبقاً للأستاذ/ة: {existing[0]}")
        else:
            cursor.execute('INSERT INTO bookings (teacher_name, subject, grade, period, booking_date, purpose, notes) VALUES (?,?,?,?,?,?,?)',
                           (t_name, t_subject, t_grade, t_period, d_str, t_purpose, t_notes))
            conn.commit()
            st.balloons()
            st.success("✅ تم استلام حجزك وتثبيته في الجدول.")
        conn.close()

    st.markdown("### 📋 سجل الحجوزات الحالي")
    conn = sqlite3.connect('lab_identity_v20.db')
    df = pd.read_sql_query("SELECT * FROM bookings", conn)
    conn.close()

    if not df.empty:
        df_ar = df.rename(columns={'teacher_name': 'المعلم', 'subject': 'المادة', 'grade': 'الصف', 'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'})
        st.write("💡 يمكنك تعديل حجزك مباشرة أدناه:")
        edited_df = st.data_editor(df_ar, column_config={"id": None}, num_rows="dynamic", use_container_width=True, key="t_edit")
        if st.button("💾 حفظ التغييرات"):
            conn = sqlite3.connect('lab_identity_v20.db')
            final_df = edited_df.rename(columns={'المعلم': 'teacher_name', 'المادة': 'subject', 'الصف': 'grade', 'الحصة': 'period', 'التاريخ': 'booking_date', 'الغرض': 'purpose', 'الملاحظات': 'notes'})
            final_df.to_sql('bookings', conn, if_exists='replace', index=False)
            conn.close()
            st.success("✅ تم تحديث الجدول")
            st.rerun()

# --- 4. واجهة أ. منير ---
else:
    st.markdown('<div style="background-color: #e0f2fe; padding: 15px; border-radius: 10px; border-right: 5px solid #0369a1;"><strong>🛠️ لوحة الإدارة الفنية - أ. منير</strong></div>', unsafe_allow_html=True)
    pwd = st.sidebar.text_input("كلمة المرور:", type="password")
    
    if pwd == "1234":
        conn = sqlite3.connect('lab_identity_v20.db')
        df_admin = pd.read_sql_query("SELECT * FROM bookings", conn)
        conn.close()

        if not df_admin.empty:
            st.markdown("### 📄 تصدير البيانات")
            c_w, c_p = st.columns(2)
            with c_w:
                df_word = df_admin.drop(columns=['id']).rename(columns={'teacher_name': 'المعلم', 'subject': 'المادة', 'grade': 'الصف', 'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'})
                html = df_word.to_html(index=False).replace('border="1"', 'border="1" style="direction:rtl; width:100%; border-collapse:collapse; text-align:right;"')
                word_file = f"<html><meta charset='utf-8'><body><h2 style='text-align:center;'>تقرير حجوزات المختبر</h2>{html}</body></html>"
                st.download_button("📝 تحميل ملف Word", data=word_file, file_name=f"حجوزات_{date.today()}.doc")
            with c_p:
                if st.button("🖨️ طباعة الجدول / PDF"):
                    st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### 🔧 إدارة البيانات الشاملة")
            df_admin_ar = df_admin.rename(columns={'teacher_name': 'المعلم', 'subject': 'المادة', 'grade': 'الصف', 'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'})
            admin_edit = st.data_editor(df_admin_ar, column_config={"id": None}, num_rows="dynamic", use_container_width=True, key="adm_edit")
            if st.button("💾 تطبيق التعديلات الإدارية"):
                conn = sqlite3.connect('lab_identity_v20.db')
                final_admin = admin_edit.rename(columns={'المعلم': 'teacher_name', 'المادة': 'subject', 'الصف': 'grade', 'الحصة': 'period', 'التاريخ': 'booking_date', 'الغرض': 'purpose', 'الملاحظات': 'notes'})
                final_admin.to_sql('bookings', conn, if_exists='replace', index=False)
                conn.close()
                st.success("✅ تمت العملية بنجاح.")
                st.rerun()
    else:
        st.warning("هذه المنطقة مخصصة لفني المختبر فقط.")
