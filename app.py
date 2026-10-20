import pandas as pd
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Hệ thống Quản lý Điểm Rèn Luyện - Lớp 12A14", layout="wide")

# --- KHỞI TẠO DỮ LIỆU MẪU TỪ EXCEL (12A14 - 55 HỌC SINH) ---
@st.cache_data
def load_students():
    try:
        df = pd.read_excel("Danh_sach_12A14.xlsx", skiprows=3)
        df.columns = ['STT', 'Lop', 'Ho_va_lot', 'Ten', 'Ngay_sinh', 'Nu']
        df = df.dropna(subset=['STT'])
        df['Ho_va_Ten'] = df['Ho_va_lot'].astype(str) + " " + df['Ten'].astype(str)
        # Phân chia ngẫu nhiên vào 5 tổ cho 55 học sinh (mỗi tổ 11 em)
        df['To'] = [f"Tổ {(i % 5) + 1}" for i in range(len(df))]
        df['Chuc_vu'] = 'Thành viên'
        # Gán mẫu ban cán sự
        df.loc[0, 'Chuc_vu'] = 'Lớp trưởng'
        df.loc[1, 'Chuc_vu'] = 'Bí thư'
        df.loc[2, 'Chuc_vu'] = 'Lớp phó'
        for i in range(1, 6):
            # Chọn đại diện làm tổ trưởng từng tổ
            to_idx = (i-1) * 11
            if to_idx < len(df):
                df.loc[to_idx, 'Chuc_vu'] = f'Tổ trưởng Tổ {i}'
        return df
    except Exception as e:
        # Dữ liệu dự phòng nếu chưa có file
        data = {
            'STT': [1, 2, 3],
            'Lop': ['12A14', '12A14', '12A14'],
            'Ho_va_Ten': ['Đào Ngọc Trâm Anh', 'Đào Thị Ngọc Ánh', 'Nguyễn Quốc Bảo'],
            'Ngay_sinh': ['01/07/2009', '13/06/2009', '24/08/2009'],
            'To': ['Tổ 1', 'Tổ 1', 'Tổ 2'],
            'Chuc_vu': ['Lớp trưởng', 'Thành viên', 'Tổ trưởng Tổ 2']
        }
        return pd.DataFrame(data)

if 'students_df' not in st.session_state:
    st.session_state.students_df = load_students()

if 'logs' not in st.session_state:
    # Lưu nhật ký cộng trừ điểm: [Tuần, Ngày, Họ và tên, Loại, Hành vi, Điểm, Người ghi]
    st.session_state.logs = []

# --- DANH MỤC HÀNH VI ---
VIOLATIONS = {
    "Đi học trễ": -2,
    "Không điểm danh trên máy": -3,
    "Mặc đồng phục không đúng quy định": -5,
    "Nghỉ học có phép buổi sáng/chiều": -1,
    "Nghỉ học không phép buổi sáng/chiều": -3,
    "Nói chuyện, mất trật tự": -1,
    "Trốn tiết, bỏ giờ": -5,
    "Ăn vụng trong lớp": -2,
    "Áo bỏ ngoài quần / Không phù hiệu": -2,
    "Chạy nhảy, đùa giỡn trong lớp/hành lang": -2,
    "Đổi chỗ, ngồi sai sơ đồ": -2,
    "Ngủ gật trong giờ học": -2,
    "Nhuộm tóc, đeo bông tai không đúng quy định": -2,
    "Nói tục, chửi thề": -2,
    "Sử dụng điện thoại trái phép": -2,
    "Tô son, sơn móng tay": -2,
    "Xả rác trong lớp/sân trường": -2,
    "Không chép bài / Không làm bài tập": -2,
    "Học môn khác / làm việc riêng": -2,
    "Trao đổi bài trong giờ kiểm tra": -5,
    "🚨 Bạo lực học đường": -10,
    "🚨 Sử dụng thuốc lá điện tử": -10,
    "🚨 Vi phạm nghiêm trọng / Đánh nhau / Hư hỏng tài sản": -10
}

BONUSES = {
    "Hoàn thành đầy đủ bài tập trong tuần": 2,
    "Tích cực phát biểu / xây dựng bài": 2,
    "Giúp đỡ bạn trong học tập": 2,
    "Có tiến bộ rõ rệt về học tập": 2,
    "Có thành tích tốt trong kiểm tra": 2,
    "Đạt thành tích nổi bật cấp lớp/trung tâm": 4
}

# --- GIAO DIỆN CHÍNH (SIDEBAR) ---
st.sidebar.title("📌 ĐIỀU HƯỚNG HỆ THỐNG")
role = st.sidebar.selectbox("Chọn vai trò đăng nhập:", [
    "👨‍🏫 Giáo viên chủ nhiệm (GVCN)", 
    "👑 Ban Cán Sự (Lớp trưởng / Tổ trưởng)", 
    "👤 Tra cứu dành cho Học sinh"
])

st.sidebar.markdown("---")
st.sidebar.info("🏫 **Lớp:** 12A14 | **GVCN:** Võ Trọng Đỉnh\n📍 **Trung tâm:** GDNN-GDTX Quận 12")

# --- 1. PHẦN GIÁO VIÊN CHỦ NHIỆM ---
if role == "👨‍🏫 Giáo viên chủ nhiệm (GVCN)":
    st.title("🛠️ Quản trị Hệ thống Điểm Rèn Luyện - GVCN")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Tổng hợp & Xếp loại", "📝 Quản lý Sổ tuần", "📋 Tạo Biên bản SHL", "⚙️ Cài đặt & Phân quyền"])
    
    df_stu = st.session_state.students_df
    
    with tab1:
        st.subheader("Bảng Tổng Hợp Điểm Rèn Luyện (Mặc định 100 điểm/tháng)")
        
        # Tính toán điểm từ logs
        scores_data = []
        for idx, row in df_stu.iterrows():
            name = row['Ho_va_Ten']
            student_logs = [l for l in st.session_state.logs if l['Hoc_sinh'] == name]
            
            total_minus = sum([l['Diem'] for l in student_logs if l['Loai'] == 'Trừ'])
            total_plus = sum([l['Diem'] for l in student_logs if l['Loai'] == 'Cộng'])
            current_score = 100 + total_plus - total_minus
            
            # Quy tắc đặc biệt
            has_severe = any("🚨" in l['Hanh_vi'] for l in student_logs)
            
            if has_severe or current_score < 50:
                rank = "CHƯA ĐẠT"
            elif current_score < 65:
                rank = "ĐẠT"
            elif current_score < 80:
                rank = "KHÁ"
            else:
                rank = "TỐT"
                
            scores_data.append({
                'STT': row['STT'],
                'Họ và tên': name,
                'Tổ': row['To'],
                'Chức vụ': row['Chuc_vu'],
                'Điểm cộng': total_plus,
                'Điểm trừ': total_minus,
                'Tổng điểm': current_score,
                'Xếp loại': rank
            })
            
        df_summary = pd.DataFrame(scores_data)
        df_summary = df_summary.sort_values(by='Tổng điểm', ascending=False).reset_index(drop=True)
        df_summary['Thứ hạng'] = df_summary.index + 1
        
        st.dataframe(df_summary[['Thứ hạng', 'STT', 'Họ và tên', 'Tổ', 'Chức vụ', 'Điểm cộng', 'Điểm trừ', 'Tổng điểm', 'Xếp loại']], use_container_width=True)
        
        # Xuất Excel
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')
        
        st.download_button("📥 Xuất file Excel tổng hợp", data=convert_df(df_summary), file_name="Tong_hop_ren_luyen_12A14.csv", mime="text/csv")

    with tab2:
        st.subheader("Nhật ký ghi nhận điểm hàng ngày")
        if len(st.session_state.logs) > 0:
            df_logs = pd.DataFrame(st.session_state.logs)
            st.dataframe(df_logs, use_container_width=True)
            if st.button("🗑️ Xóa toàn bộ nhật ký"):
                st.session_state.logs = []
                st.rerun()
        else:
            st.info("Chưa có ghi nhận vi phạm hoặc điểm cộng nào trong tuần.")

    with tab3:
        st.subheader("Tự động tạo Biên bản Sinh hoạt Lớp Hàng Tuần")
        tuan_chon = st.selectbox("Chọn tuần sinh hoạt:", ["Tuần 1", "Tuần 2", "Tuần 3", "Tuần 4"])
        ngay_bd = st.text_input("Từ ngày (dd/mm/yyyy):", "12/09/2026")
        ngay_kt = st.text_input("Đến ngày (dd/mm/yyyy):", "18/09/2026")
        
        if st.button("✨ Tạo Biên Bản Chuẩn"):
            st.markdown(f"""
            ### 🏫 TRUNG TÂM GDNN-GDTX QUẬN 12
            #### CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
            #### Độc lập – Tự do – Hạnh phúc
            ---
            ### BIÊN BẢN SINH HOẠT LỚP 12A14 - {tuan_chon.upper()}
            *(Từ ngày {ngay_bd} đến ngày {ngay_kt})*
            
            #### I. Sơ kết {tuan_chon}:
            * **Tổng điểm chung của lớp:** Ổn định, duy trì nền nếp tốt.
            * **Những học sinh chưa thực hiện tốt nội quy:**
            """)
            
            violation_logs = [l for l in st.session_state.logs if l['Loai'] == 'Trừ']
            if violation_logs:
                for idx, v in enumerate(violation_logs, 1):
                    st.write(f"{idx}. **{v['Hoc_sinh']}** - Lỗi: {v['Hanh_vi']} ({v['Ngay']}) -> Trừ {v['Diem']} điểm")
            else:
                st.write("*(Không có học sinh vi phạm trọng điểm trong tuần)*")
                
            st.markdown("""
            * **Biện pháp giáo dục của GVCN:** Đối với học sinh vi phạm lỗi không nghiêm trọng lần đầu tiến hành nhắc nhở. Tái phạm cho viết bản kiểm điểm và mời phụ huynh phối hợp giáo dục.
            
            #### II. Biểu dương học viên hoạt động tích cực trong tuần:
            """)
            bonus_logs = [l for l in st.session_state.logs if l['Loai'] == 'Cộng']
            if bonus_logs:
                for idx, b in enumerate(bonus_logs, 1):
                    st.write(f"{idx}. **{b['Hoc_sinh']}** - Thành tích: {b['Hanh_vi']} ({b['Ngay']}) -> Cộng {b['Diem']} điểm")
            else:
                st.write("*(Tuyên dương toàn thể lớp giữ vững tinh thần học tập)*")
                
            st.markdown("""
            #### III. Kế hoạch tuần tới:
            1. Tiếp tục thực hiện tốt nội quy nhà trường.
            2. Hoàn thành tốt nhiệm vụ học tập, ôn tập kiểm tra.
            3. Tham gia đầy đủ các phong trào thi đua chào mừng ngày lễ.
            
            *Trung Mỹ Tây, Ngày ... tháng ... năm 2026*  
            **GIÁO VIÊN CHỦ NHIỆM**  
            *(Ký và xác nhận)*  
            **Võ Trọng Đỉnh**
            """)

    with tab4:
        st.subheader("⚙️ Cài đặt & Phân quyền Ban Cán Sự")
        st.write("Danh sách học sinh hiện tại và chức vụ:")
        st.dataframe(df_stu[['STT', 'Ho_va_Ten', 'To', 'Chuc_vu']], use_container_width=True)

# --- 2. PHẦN BAN CÁN SỰ (LỚP TRƯỞNG & TỔ TRƯỞNG) ---
elif role == "👑 Ban Cán Sự (Lớp trưởng / Tổ trưởng)":
    st.title("👑 Cổng Ghi Nhận Thi Đua - Ban Cán Sự")
    
    bcs_role = st.radio("Bạn là ai?", ["Lớp trưởng (Quản lý toàn lớp)", "Tổ trưởng (Quản lý theo tổ)"])
    df_stu = st.session_state.students_df
    
    if bcs_role == "Tổ trưởng (Quản lý theo tổ)":
        to_chon = st.selectbox("Chọn tổ của bạn quản lý:", df_stu['To'].unique())
        df_target = df_stu[df_stu['To'] == to_chon]
    else:
        df_target = df_stu
        
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        ngay_ghi = st.date_input("Chọn ngày ghi nhận:", datetime.now())
        tuan_hoc = st.selectbox("Chọn tuần:", ["Tuần 1", "Tuần 2", "Tuần 3", "Tuần 4"])
        hs_chon = st.selectbox("Chọn học sinh:", df_target['Ho_va_Ten'].tolist())
        
    with col2:
        loai_ghi = st.radio("Loại điểm:", ["Điểm Trừ (Vi phạm)", "Điểm Cộng (Khen thưởng)"])
        if loai_ghi == "Điểm Trừ (Vi phạm)":
            hanh_vi = st.selectbox("Chọn lỗi vi phạm:", list(VIOLATIONS.keys()))
            diem_so = VIOLATIONS[hanh_vi]
            loai = "Trừ"
        else:
            hanh_vi = st.selectbox("Chọn thành tích:", list(BONUSES.keys()))
            diem_so = BONUSES[hanh_vi]
            loai = "Cộng"
            
    if st.button("💾 Lưu Ghi Nhận Thi Đua"):
        st.session_state.logs.append({
            'Tuan': tuan_hoc,
            'Ngay': ngay_ghi.strftime('%d/%m/%Y'),
            'Hoc_sinh': hs_chon,
            'Loai': loai,
            'Hanh_vi': hanh_vi,
            'Diem': abs(diem_so)
        })
        st.success(f"Đã lưu thành công cho học sinh **{hs_chon}** ({hanh_vi}: {diem_so} điểm)!")

# --- 3. PHẦN HỌC SINH ---
else:
    st.title("👤 Tra cứu Điểm Rèn Luyện Cá Nhân")
    df_stu = st.session_state.students_df
    hs_ten = st.selectbox("Chọn tên của bạn để tra cứu:", sorted(df_stu['Ho_va_Ten'].tolist()))
    
    if hs_ten:
        student_logs = [l for l in st.session_state.logs if l['Hoc_sinh'] == hs_ten]
        total_minus = sum([l['Diem'] for l in student_logs if l['Loai'] == 'Trừ'])
        total_plus = sum([l['Diem'] for l in student_logs if l['Loai'] == 'Cộng'])
        current_score = 100 + total_plus - total_minus
        
        has_severe = any("🚨" in l['Hanh_vi'] for l in student_logs)
        if has_severe or current_score < 50:
            rank = "CHƯA ĐẠT"
        elif current_score < 65:
            rank = "ĐẠT"
        elif current_score < 80:
            rank = "KHÁ"
        else:
            rank = "TỐT"
            
        st.markdown(f"### 📌 Kết quả rèn luyện của em: **{hs_ten}**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Điểm hiện tại", f"{current_score} / 100")
        c2.metric("Điểm cộng", f"+{total_plus}")
        c3.metric("Điểm trừ", f"-{total_minus}")
        c4.metric("Xếp loại", rank)
        
        st.markdown("#### 📜 Chi tiết lịch sử các khoản điểm cộng/trừ:")
        if student_logs:
            df_hs_logs = pd.DataFrame(student_logs)
            st.dataframe(df_hs_logs[['Tuan', 'Ngay', 'Loai', 'Hanh_vi', 'Diem']], use_container_width=True)
        else:
            st.info("Em chưa có ghi nhận vi phạm hay điểm thưởng nào trong tháng. Cứ tiếp tục phát huy nhé!")