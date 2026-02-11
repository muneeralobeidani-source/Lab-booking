import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('lab_luxury_v17.db')
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

# إعدادات جمالية للصفحة
st.set_page_config(page_title="مختبر أ. منير الذكي", layout="wide", initial_sidebar_state="expanded")

# إضافة CSS مخصص لتحسين الواجهة
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #007bff; color: white; }
    .stDownloadButton>button { border-radius: 20px; background-color: #28a745; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧪 مختبر الأستاذ منير المتطور")
st.caption("نظام الحجز الذكي - الدقة، السرعة، والسهولة")

# --- القائمة الجانبية ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1048/1048953.png", width=100)
user_role = st.sidebar.radio("👤 دخول المستخدم:", ["بوابة المعلمين", "لوحة الفني (أ. منير)"])

# --- واجهة المعلمين ---
if user_role == "بوابة المعلمين":
    col_info, col_form = st.columns([1, 2])
    
    with col_info:
        st.info("💡 **تعليمات:** يرجى التأكد من اختيار الحصة والتاريخ بدقة لتجنب التعارض.")
        st.image("https://cdn-icons-png.flaticon.com/512/3067/3067451.png")

    with col_form:
        with st.form("booking_form", clear_on_submit=True):
            st.subheader("📝 طلب حجز جديد")
            t_name = st.text_input("👤 اسم المعلم")
            c1, c2, c3 = st.columns(3)
            with c1: t_subject = st.selectbox("📚 المادة", ["علوم", "فيزياء", "كيمياء", "أحياء", "آخر"])
            with c2: t_grade = st.selectbox("🏫 الصف", [str(i) for i in range(1, 13)])
            with c3: t_period = st.selectbox("⏰ الحصة", [str(i) for i in range(1, 9)])
            
            t_date = st.date_input("📅 التاريخ", date.today())
            t_purpose = st.radio("🎯 الغرض", ["تجربة عملية", "عرض تعليمي"], horizontal=True)
            t_notes = st.text_area("🗒️ ملاحظات إضافية")
            
            submit = st.form_submit_button("إرسال طلب الحجز")

    if submit and t_name:
        d_str = t_date.strftime('%Y-%m-%d')
        conn = sqlite3.connect('lab_luxury_v17.db')
        cursor = conn.cursor()
        cursor.execute('SELECT teacher_name FROM bookings WHERE period = ? AND booking_date = ?', (t_period, d_str))
        existing = cursor.fetchone()
        
        if existing:
            st.error(f"❌ تعارض! المختبر محجوز مسبقاً للأستاذ/ة: {existing[0]}")
        else:
            cursor.execute('INSERT INTO bookings (teacher_name, subject, grade, period, booking_date, purpose, notes) VALUES (?,?,?,?,?,?,?)',
                           (t_name, t_subject, t_grade, t_period, d_str, t_purpose, t_notes))
            conn.commit()
            st.balloons() # لمسة شيقة: احتفال بالنجاح
            st.success(f"🎊 تم الحجز بنجاح أستاذ {t_name}!")
        conn.close()

    st.markdown("---")
    st.subheader("📅 جدول المواعيد التفاعلي")
    conn = sqlite3.connect('lab_luxury_v17.db')
    df = pd.read_sql_query("SELECT id, teacher_name, subject, grade, period, booking_date, purpose, notes FROM bookings", conn)
    conn.close()

    if not df.empty:
        df_ar = df.rename(columns={'teacher_name': 'المعلم', 'subject': 'المادة', 'grade': 'الصف', 'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'})
        edited_df = st.data_editor(df_ar, column_config={"id": None}, num_rows="dynamic", use_container_width=True)
        if st.button("💾 حفظ تعديلات المعلمين"):
            conn = sqlite3.connect('lab_luxury_v17.db')
            final_df = edited_df.rename(columns={'المعلم': 'teacher_name', 'المادة': 'subject', 'الصف': 'grade', 'الحصة': 'period', 'التاريخ': 'booking_date', 'الغرض': 'purpose', 'الملاحظات': 'notes'})
            final_df.to_sql('bookings', conn, if_exists='replace', index=False)
            conn.close()
            st.toast("تم تحديث البيانات!", icon='✅')

# --- واجهة أ. منير ---
else:
    st.subheader("🛠️ الإدارة العليا - أ. منير")
    pwd = st.sidebar.text_input("رمز الدخول:", type="password")
    
    if pwd == "1234":
        conn = sqlite3.connect('lab_luxury_v17.db')
        df_admin = pd.read_sql_query("SELECT * FROM bookings", conn)
        conn.close()

        # إحصائيات سريعة (لمسة فريدة)
        col_stat1, col_stat2 = st.columns(2)
        col_stat1.metric("إجمالي الحجوزات", len(df_admin))
        col_stat2.metric("حجوزات اليوم", len(df_admin[df_admin['booking_date'] == str(date.today())]))

        st.markdown("### 📤 استخراج التقارير")
        c_word, c_print = st.columns(2)
        with c_word:
            html_table = df_admin.drop(columns=['id']).to_html(index=False).replace('border="1"', 'border="1" style="direction:rtl; width:100%; text-align:right;"')
            word_data = f"<html><meta charset='utf-8'><body><h2 style='text-align:center;'>تقرير المختبر</h2>{html_table}</body></html>"
            st.download_button("📝 تصدير لـ Word", data=word_data, file_name=f"حجوزات_{date.today()}.doc")
        with c_print:
            if st.button("🖨️ طباعة سريعة"):
                st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

        st.markdown("---")
        st.write("🔧 **تحكم الفني الكامل:**")
        df_admin_ar = df_admin.rename(columns={'teacher_name': 'المعلم', 'subject': 'المادة', 'grade': 'الصف', 'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'})
        admin_edit = st.data_editor(df_admin_ar, column_config={"id": None}, num_rows="dynamic", use_container_width=True)
        
        if st.button("💾 حفظ التعديلات الإدارية"):
            conn = sqlite3.connect('lab_luxury_v17.db')
            final_admin_df = admin_edit.rename(columns={'المعلم': 'teacher_name', 'المادة': 'subject', 'الصف': 'grade', 'الحصة': 'period', 'التاريخ': 'booking_date', 'الغرض': 'purpose', 'الملاحظات': 'notes'})
            final_admin_df.to_sql('bookings', conn, if_exists='replace', index=False)
            conn.close()
            st.success("تم تحديث النظام الإداري.")
    else:
        st.warning("الرجاء إدخال الرمز السري.")
