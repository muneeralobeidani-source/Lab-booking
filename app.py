import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('lab_system_v19.db')
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

# --- لمسة التنسيق اللوني (CSS المطور) ---
st.markdown("""
    <style>
    /* تغيير خلفية الصفحة */
    .stApp {
        background-color: #F8F9FB;
    }
    
    /* تنسيق العناوين */
    h1 {
        color: #1E3A8A; /* أزرق داكن احترافي */
        font-family: 'Arial';
        text-align: center;
        padding-bottom: 20px;
        border-bottom: 2px solid #E5E7EB;
    }
    
    /* تنسيق الأزرار (تأكيد الحجز) */
    .stButton>button {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        border: None;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #1E40AF;
        transform: scale(1.02);
    }
    
    /* تنسيق زر التحميل (وورد) */
    .stDownloadButton>button {
        background-color: #059669 !important;
        color: white !important;
        border-radius: 8px !important;
    }

    /* تنسيق الحقول الإدخال */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        border-radius: 8px !important;
    }
    
    /* إخفاء القوائم عند الطباعة */
    @media print {
        .stButton, .stSidebar, .stRadio, .stForm, .stHeader, .no-print { display: none !important; }
        .main { width: 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# العنوان
st.title("📑 نظام حجز المختبر")

# --- 2. القائمة الجانبية ---
st.sidebar.markdown("<h2 style='text-align: center; color: #1E3A8A;'>القائمة</h2>", unsafe_allow_html=True)
user_role = st.sidebar.radio("اختر نوع المستخدم:", ["واجهة المعلمين (حجز وتعديل)", "فني المختبر (إدارة وطباعة)"])

# --- 3. واجهة المعلمين ---
if user_role == "واجهة المعلمين (حجز وتعديل)":
    with st.container():
        st.markdown("<div style='background-color: white; padding: 25px; border-radius: 15px; border: 1px solid #E5E7EB;'>", unsafe_allow_html=True)
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
            submit_btn = st.form_submit_button("إرسال طلب الحجز")
        st.markdown("</div>", unsafe_allow_html=True)

    if submit_btn and t_name:
        d_str = t_date.strftime('%Y-%m-%d')
        conn = sqlite3.connect('lab_system_v19.db')
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
            st.success("✅ تم تأكيد حجزك بنجاح")
        conn.close()

    st.markdown("---")
    st.subheader("📋 جدول المواعيد")
    conn = sqlite3.connect('lab_system_v19.db')
    df = pd.read_sql_query("SELECT * FROM bookings", conn)
    conn.close()

    if not df.empty:
        df_ar = df.rename(columns={'teacher_name': 'المعلم', 'subject': 'المادة', 'grade': 'الصف', 'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'})
        # تلوين الجدول بشكل تفاعلي
        edited_df = st.data_editor(df_ar, column_config={"id": None}, num_rows="dynamic", use_container_width=True, key="t_edit")
        if st.button("💾 حفظ التعديلات"):
            conn = sqlite3.connect('lab_system_v19.db')
            final_df = edited_df.rename(columns={'المعلم': 'teacher_name', 'المادة': 'subject', 'الصف': 'grade', 'الحصة': 'period', 'التاريخ': 'booking_date', 'الغرض': 'purpose', 'الملاحظات': 'notes'})
            final_df.to_sql('bookings', conn, if_exists='replace', index=False)
            conn.close()
            st.success("✅ تم تحديث البيانات")
            st.rerun()

# --- 4. واجهة فني المختبر ---
else:
    st.markdown("<div style='background-color: #EFF6FF; padding: 20px; border-radius: 10px; color: #1E3A8A;'><strong>🛠️ لوحة تحكم فني المختبر (أ. منير)</strong></div>", unsafe_allow_html=True)
    pwd = st.sidebar.text_input("كلمة المرور:", type="password")
    
    if pwd == "1234":
        conn = sqlite3.connect('lab_system_v19.db')
        df_admin = pd.read_sql_query("SELECT * FROM bookings", conn)
        conn.close()

        if not df_admin.empty:
            st.markdown("### 📄 خيارات التصدير")
            col_w, col_p = st.columns(2)
            with col_w:
                df_for_word = df_admin.drop(columns=['id']).rename(columns={'teacher_name': 'المعلم', 'subject': 'المادة', 'grade': 'الصف', 'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'})
                html_table = df_for_word.to_html(index=False).replace('border="1"', 'border="1" style="direction:rtl; width:100%; border-collapse:collapse; text-align:right; font-family: Arial; background-color: white;"')
                word_data = f"<html><meta charset='utf-8'><body style='font-family: Arial;'> <h2 style='text-align:center;'>جدول حجوزات المختبر</h2>{html_table}</body></html>"
                st.download_button("📝 تنزيل كملف Word", data=word_data, file_name=f"حجوزات_{date.today()}.doc")
            with col_p:
                if st.button("🖨️ طباعة الجدول / PDF"):
                    st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

            st.markdown("---")
            st.write("🔧 **الإدارة الكاملة للبيانات:**")
            df_admin_ar = df_admin.rename(columns={'teacher_name': 'المعلم', 'subject': 'المادة', 'grade': 'الصف', 'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'})
            admin_edited = st.data_editor(df_admin_ar, column_config={"id": None}, num_rows="dynamic", use_container_width=True, key="adm_edit")
            if st.button("💾 حفظ التعديلات النهائية"):
                conn = sqlite3.connect('lab_system_v19.db')
                final_admin_df = admin_edited.rename(columns={'المعلم': 'teacher_name', 'المادة': 'subject', 'الصف': 'grade', 'الحصة': 'period', 'التاريخ': 'booking_date', 'الغرض': 'purpose', 'الملاحظات': 'notes'})
                final_admin_df.to_sql('bookings', conn, if_exists='replace', index=False)
                conn.close()
                st.success("✅ تم الحفظ بنجاح")
                st.rerun()
    else:
        st.warning("يرجى إدخال كلمة المرور للوصول للصلاحيات.")
