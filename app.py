import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# 1. إعداد الصفحة والهوية البصرية
st.set_page_config(page_title="حجز المختبر", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(to bottom, #f0f2f5, #ffffff); }
    .main-title {
        color: #1e3a8a; text-align: center; font-family: 'Segoe UI'; font-weight: bold;
        padding: 20px; background: white; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 30px;
    }
    .custom-card {
        background-color: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); border: 1px solid #e5e7eb; margin-bottom: 20px;
    }
    .stButton>button { background-color: #1e3a8a; color: white; border-radius: 10px; font-weight: bold; width: 100%; }
    div.stDownloadButton > button { background-color: #10b981 !important; color: white !important; border-radius: 10px !important; width: 100%; }
    @media print { .stButton, .stSidebar, .stRadio, .stForm, .stHeader { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">📑 نظام حجز المختبر (الربط السحابي الآمن)</div>', unsafe_allow_html=True)

# 2. الربط السحابي مع Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # قراءة البيانات - تأكد من وجود العناوين الصحيحة في ملفك
    df = conn.read(ttl="0") 
except Exception as e:
    st.error("⚠️ خطأ في الاتصال بالسحابة. تأكد من إعداد الـ Secrets بشكل صحيح.")
    st.stop()

# 3. القائمة الجانبية
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>👤 الدخول</h2>", unsafe_allow_html=True)
    user_role = st.radio("اختر الواجهة:", ["بوابة المعلمين", "لوحة التحكم (أ. منير)"])
    st.markdown("---")
    st.info("جميع الحجوزات تُحفظ تلقائياً في قاعدة بيانات جوجل السحابية.")

# 4. واجهة المعلمين
if user_role == "بوابة المعلمين":
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("📝 تسجيل حجز جديد")
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
        t_notes = st.text_area("🗒️ ملاحظات إضافية")
        submit_btn = st.form_submit_button("تأكيد وإرسال الحجز")
    st.markdown('</div>', unsafe_allow_html=True)

    if submit_btn and t_name:
        d_str = t_date.strftime('%Y-%m-%d')
        # فحص التعارض
        conflict = df[(df['period'].astype(str) == str(t_period)) & (df['booking_date'].astype(str) == d_str)]
        
        if not conflict.empty:
            st.error(f"🚨 عذراً، المختبر محجوز مسبقاً للأستاذ/ة: {conflict.iloc[0]['teacher_name']}")
        else:
            new_row = pd.DataFrame([{
                "teacher_name": t_name, "subject": t_subject, "grade": t_grade,
                "period": t_period, "booking_date": d_str, "purpose": t_purpose, "notes": t_notes
            }])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=updated_df)
            st.balloons()
            st.success("✅ تم الحجز بنجاح وحفظه سحابياً.")
            st.rerun()

    st.markdown("### 📋 سجل الحجوزات الحالي")
    if not df.empty:
        df_ar = df.rename(columns={'teacher_name': 'المعلم', 'subject': 'المادة', 'grade': 'الصف', 'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'})
        edited_df = st.data_editor(df_ar, num_rows="dynamic", use_container_width=True, key="t_edit")
        if st.button("💾 حفظ التعديلات"):
            final_df = edited_df.rename(columns={'المعلم': 'teacher_name', 'المادة': 'subject', 'الصف': 'grade', 'الحصة': 'period', 'التاريخ': 'booking_date', 'الغرض': 'purpose', 'الملاحظات': 'notes'})
            conn.update(data=final_df)
            st.success("✅ تم التحديث في السحابة.")
            st.rerun()

# 5. واجهة أ. منير
else:
    st.markdown('<div style="background-color: #e0f2fe; padding: 15px; border-radius: 10px;"><strong>🛠️ لوحة الإدارة الفنية - أ. منير</strong></div>', unsafe_allow_html=True)
    pwd = st.sidebar.text_input("كلمة المرور:", type="password")
    if pwd == "1234":
        if not df.empty:
            st.markdown("### 📄 التقارير والطباعة")
            c_w, c_p = st.columns(2)
            with c_w:
                # تصدير ملف إكسل سريع كنسخة إضافية
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📂 تحميل نسخة إكسل احتياطية", data=csv, file_name=f"backup_{date.today()}.csv")
            with c_p:
                if st.button("🖨️ طباعة الجدول"): st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
            
            st.markdown("---")
            st.write("🔧 **الإدارة الكاملة (تعديل/حذف من السحابة):**")
            admin_df_ar = df.rename(columns={'teacher_name': 'المعلم', 'subject': 'المادة', 'grade': 'الصف', 'period': 'الحصة', 'booking_date': 'التاريخ', 'purpose': 'الغرض', 'notes': 'الملاحظات'})
            admin_edit = st.data_editor(admin_df_ar, num_rows="dynamic", use_container_width=True, key="adm_edit")
            if st.button("💾 تطبيق التعديلات الإدارية النهائية"):
                final_admin = admin_edit.rename(columns={'المعلم': 'teacher_name', 'المادة': 'subject', 'الصف': 'grade', 'الحصة': 'period', 'التاريخ': 'booking_date', 'الغرض': 'purpose', 'الملاحظات': 'notes'})
                conn.update(data=final_admin)
                st.success("✅ تم مزامنة التغييرات مع Google Sheets.")
                st.rerun()
    else:
        st.warning("يرجى إدخال كلمة المرور.")
