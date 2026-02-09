#!/usr/bin/env python
# coding: utf-8

# ## Survey
# 
# null

# In[1]:


import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import re
import requests
from io import BytesIO
import time
import base64
import os
# --- 1. CẤU HÌNH ---
DATA_SHEET_URL = "https://docs.google.com/spreadsheets/d/1DMgxkDSp_dq7IMzEmHdGK-nypIc_PLSsmTUIwFCXqZ8/edit" # Link Sheet Kết Quả
CONFIG_SHEET_URL = "https://docs.google.com/spreadsheets/d/1nNJI1oxEhgYtNCk1pdEFyIR6M4UPrfjRw1F_rljyAHM/edit" # Link Sheet Config
EMAIL_DOMAIN = "@winmart.masangroup.com" # Điền đuôi email công ty

# --- 2. CÁC HÀM TIỆN ÍCH (UTILS) ---

def sanitize_sheet_name(name):
    """Làm sạch tên để đặt tên cho Tab Google Sheet (bỏ ký tự cấm)."""
    # Thay thế các ký tự không được phép bằng gạch dưới
    clean_name = re.sub(r'[\\/*?:\[\]]', '_', name)
    return clean_name

def generate_target_columns(visual_items, filter_items):
    """
    Tự động tạo danh sách cột tiêu đề dựa trên danh sách câu hỏi hiện có.
    """
    # 1. Các cột cố định đầu tiên
    cols = [
        "Timestamp", 
        "User Account", 
        "Report Name",
        "1. Tần suất truy cập", 
        "2. Mục đích truy cập"
    ]
    
    # 2. Cột động cho VISUAL
    for label, _, _ in visual_items:
        cols.append(f"Rating: {label}")
        cols.append(f"Issues: {label}")
        
    # 3. Cột Feedback Visual
    cols.append("5. Đề xuất cải thiện Visual")
    
    # 4. Cột động cho FILTER
    for label, _, _ in filter_items:
        cols.append(f"Rating Filter: {label}")
        
    # 5. Cột Feedback Filter
    cols.append("7. Đề xuất cải thiện Filter")
    
    return cols

@st.cache_data(show_spinner=False)
def load_report_list():
    """Đọc danh sách báo cáo từ file .txt nằm cùng thư mục."""
    file_path = "list_reports.txt"
    if not os.path.exists(file_path):
        return ["Mặc định (Không tìm thấy file list_reports.txt)"]
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        return [f"Lỗi đọc file: {e}"]

@st.cache_data(show_spinner=False)
def get_image_as_base64(drive_link):
    """Tải ảnh từ Google Drive và chuyển thành Base64 (Chống lỗi 403)."""
    if not drive_link: return None
    match = re.search(r'[/\?&](?:d|id|file/d/)=([a-zA-Z0-9_-]+)', drive_link)
    if not match: return None
    file_id = match.group(1)
    url = f"https://drive.google.com/uc?export=view&id={file_id}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            encoded = base64.b64encode(response.content).decode()
            return f"data:image/jpeg;base64,{encoded}"
    except: pass
    return None

# --- 3. KẾT NỐI GOOGLE SHEET ---

def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"]) 
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

@st.cache_resource
def get_config_data():
    """Lấy toàn bộ dữ liệu cấu hình Visual/Filter."""
    try:
        client = get_gspread_client()
        worksheet = client.open_by_url(CONFIG_SHEET_URL).worksheet("Config_Visual")
        return worksheet.get_all_records()
    except Exception as e:
        return []

def get_or_create_sheet(report_name, header_columns):
    """
    Tìm Tab theo tên báo cáo. Nếu chưa có thì TẠO MỚI và điền Header.
    """
    client = get_gspread_client()
    sh = client.open_by_url(DATA_SHEET_URL)
    
    safe_name = sanitize_sheet_name(report_name)
    
    try:
        # Cố gắng mở Sheet hiện có
        worksheet = sh.worksheet(safe_name)
    except gspread.WorksheetNotFound:
        # Nếu chưa có -> Tạo mới
        # rows=100 cho nhẹ, cols=độ dài header
        worksheet = sh.add_worksheet(title=safe_name, rows=100, cols=len(header_columns))
        # Ghi dòng tiêu đề ngay lập tức
        worksheet.append_row(header_columns)
        
    return worksheet

# --- 4. CẤU HÌNH TRANG & CSS ---
st.set_page_config(page_title="Khảo sát BI Dashboard CMC", layout="wide")

st.markdown("""
<script>
    window.toggleZoom = function(element) {
        // Kiểm tra trạng thái hiện tại (đang zoom hay chưa?)
        // Chúng ta dùng thuộc tính data-zoomed="true/false" để theo dõi
        const isZoomed = element.getAttribute('data-zoomed') === 'true';

        if (isZoomed) {
            // Đang to -> Thu nhỏ lại
            element.style.transform = "scale(1)";
            element.setAttribute('data-zoomed', 'false');
            element.style.cursor = "zoom-in"; // Đổi con trỏ thành kính lúp cộng
            element.style.zIndex = "100";     // Trả về lớp bình thường
        } else {
            // Đang nhỏ -> Phóng to
            element.style.transform = "scale(2)"; // Phóng to gấp 2 lần (bạn có thể chỉnh số này)
            element.setAttribute('data-zoomed', 'true');
            element.style.cursor = "zoom-out"; // Đổi con trỏ thành kính lúp trừ
            element.style.zIndex = "99999";    // Đưa ảnh lên trên cùng để không bị che
        }
    }
</script>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    /* CSS Tooltip thông minh (Tự co giãn) */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
        color: #2E86C1;
        font-weight: 600;
        font-size: 16px;
        padding: 12px;
        border-radius: 8px;
        background-color: #f9f9f9;
        border: 1px solid transparent;
        transition: all 0.2s ease;
        width: 100%; 
    }
    .tooltip:hover {
        background-color: #e6f3ff;
        border-color: #b3d9ff;
        z-index: 1000; 
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: max-content;
        max-width: 650px;
        min-width: 300px;
        background-color: #ffffff;
        color: #333;
        text-align: left;
        border-radius: 8px;
        padding: 15px;
        position: absolute;
        z-index: 9999;
        top: 50%;
        left: 105%;
        transform: translateY(-50%);
        opacity: 0;
        transition: opacity 0.3s;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.2);
        border: 1px solid #ddd;
        font-weight: normal;
        font-size: 14px;
        line-height: 1.5;
        white-space: normal;
    }
    .tooltip .tooltiptext::after {
        content: "";
        position: absolute;
        top: 50%;
        right: 100%; 
        margin-top: -8px;
        border-width: 8px;
        border-style: solid;
        border-color: transparent #ffffff transparent transparent; 
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    .tooltip-img {
        width: auto;
        height: auto;
        max-width: 100%;
        max-height: 450px;
        
        display: block;
        margin: 0 auto 12px auto;
        border-radius: 6px;
        border: 1px solid #eee;
        
        /* Hiệu ứng chuyển động mượt */
        transition: transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        transform-origin: center center;
        cursor: zoom-in; /* Hiện kính lúp cộng */
        position: relative;
        z-index: 100;
    }

    /* 5. LOGIC ZOOM */
    
    /* Ẩn cái ô checkbox đi (chỉ dùng logic của nó) */
    .zoom-checkbox {
        display: none;
    }

    /* Khi checkbox được tick -> Ảnh nằm ngay sau Label sẽ phóng to */
    .zoom-checkbox:checked + label .tooltip-img {
        transform: scale(2.0); /* Phóng to gấp 2 lần */
        cursor: zoom-out;      /* Đổi con trỏ thành kính lúp trừ */
        z-index: 9999;         /* Nổi lên trên cùng */
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); /* Đổ bóng cho đẹp */
    }
    .section-header { font-size: 22px; font-weight: bold; margin-top: 40px; margin-bottom: 20px; color: #262730; border-bottom: 2px solid #f0f2f6; padding-bottom: 10px; }
    .small-text { font-size: 13px; color: #666; font-style: italic; }
    .thank-you-box { text-align: center; padding: 50px; background-color: #f0f8ff; border-radius: 15px; margin-top: 20px; }
    .thank-you-title { color: #2E86C1; font-size: 32px; font-weight: bold; }
    .thank-you-text { font-size: 18px; color: #555; margin-top: 15px; }
    [data-testid="InputInstructions"] { display: none; }
</style>
""", unsafe_allow_html=True)

# --- 5. HÀM RENDER GIAO DIỆN ---
img_placeholder = "https://via.placeholder.com/400x200?text=No+Image"
issues_list = ["Cách trình bày/biểu đồ quá phức tạp", "Số liệu thường xuyên sai lệch", "Font chữ nhỏ, màu sắc khó nhìn", "Cần số liệu này nhưng không xem được", "Khó thao tác", "Tốc độ tải quá chậm", "Không hiển thị tốt trên thiết bị của tôi"]

def render_combined_visual_row(index, label, description, raw_link):
    base64_img = get_image_as_base64(raw_link)
    display_src = base64_img if base64_img else img_placeholder
    
    # Tạo ID duy nhất
    zoom_id = f"zoom-vis-{index}"

    col1, col2 = st.columns([7, 3])
    with col1:
        s1, s2 = st.columns([2, 5])
        with s1:
            # 👇 QUAN TRỌNG:
            # 1. HTML viết sát lề trái.
            # 2. onmouseleave gọi thẳng ID để tắt checkbox (checked = false).
            tooltip_html = f"""<div class="tooltip" onmouseleave="document.getElementById('{zoom_id}').checked = false">
<span> {label}</span>
<span class="tooltiptext">
<input type="checkbox" id="{zoom_id}" class="zoom-checkbox">
<label for="{zoom_id}">
<img src="{display_src}" class="tooltip-img" alt="Minh họa">
</label>
<div style="text-align: center; font-size: 11px; color: #888; margin-top: 5px;">(Bấm để Phóng to/Thu nhỏ)</div>
<br>{description}<br>
</span>
</div>""" 
            # 👆 Kết thúc HTML
            
            st.markdown(tooltip_html, unsafe_allow_html=True)
            
    with col2:
        st.markdown(f"<span class='small-text' style='color:#D35400'>Mức độ cần thiết:</span>", unsafe_allow_html=True)
        rating_options = ["Rất không cần thiết", "Không cần thiết", "Bình thường", "Cần thiết", "Rất cần thiết"]
        st.selectbox(f"Rating {label}", rating_options, key=f"vis_rating_{index}", index=None, placeholder="Chọn mức độ...", label_visibility="collapsed")
        
        st.markdown(f"<span class='small-text' style='color:#D35400'>Vấn đề tồn đọng (nếu có, có thể chọn nhiều hơn 1 vấn đề):</span>", unsafe_allow_html=True)
        st.multiselect(f"Issues {label}", issues_list, key=f"vis_issue_{index}", label_visibility="collapsed", placeholder="Chọn vấn đề...")
    
    st.markdown("<hr style='margin: 15px 0; border-top: 1px solid #f0f2f6;'>", unsafe_allow_html=True)


def render_filter_row(index, label, description, raw_link):
    base64_img = get_image_as_base64(raw_link)
    display_src = base64_img if base64_img else img_placeholder
    
    # Tạo ID duy nhất (Khác với Visual)
    zoom_id = f"zoom-fil-{index}"

    col1, col2 = st.columns([7, 3])
    with col1:
        s1, s2 = st.columns([2, 5])
        with s1:
            # 👇 QUAN TRỌNG: onmouseleave gọi thẳng ID 👇
            tooltip_html = f"""<div class="tooltip" onmouseleave="document.getElementById('{zoom_id}').checked = false">
<span> {label}</span>
<span class="tooltiptext">
<input type="checkbox" id="{zoom_id}" class="zoom-checkbox">
<label for="{zoom_id}">
<img src="{display_src}" class="tooltip-img" alt="Minh họa">
</label>
<div style="text-align: center; font-size: 11px; color: #888; margin-top: 5px;">(Bấm để Phóng to • Di chuột ra ngoài để Thu nhỏ)</div>
<br>{description}<br>
</span>
</div>"""
            
            st.markdown(tooltip_html, unsafe_allow_html=True)
            
    with col2:
        st.markdown(f"<span class='small-text' style='color:#D35400'>Mức độ cần thiết:</span>", unsafe_allow_html=True)
        rating_options = ["Rất không cần thiết", "Không cần thiết", "Bình thường", "Cần thiết", "Rất cần thiết"]
        st.selectbox(f"Filter Rating {label}", rating_options, key=f"fil_rating_{index}", index=None, placeholder="Chọn mức độ...", label_visibility="collapsed")

    st.markdown("<hr style='margin: 15px 0; border-top: 1px dashed #eee;'>", unsafe_allow_html=True)

# --- 6. LOGIC CHÍNH (MAIN APP) ---

if 'submitted' not in st.session_state:
    st.session_state['submitted'] = False

if st.session_state['submitted']:
    st.markdown("""
    <div class="thank-you-box">
        <div class="thank-you-title">🎉 Đã gửi thành công!</div>
        <div class="thank-you-text">
            Cảm ơn anh/chị đã dành thời gian đóng góp ý kiến.<br>
            Chúng tôi sẽ ghi nhận và cải thiện Dashboard trong thời gian sớm nhất.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Điền lại khảo sát khác"):
        st.session_state['submitted'] = False
        st.rerun()

else:
    st.title("Danh sách các báo cáo cần khảo sát")
    
    # -----------------------------------------------
    # BƯỚC 1: CHỌN BÁO CÁO (Ở NGOÀI FORM)
    # -----------------------------------------------
    report_options = load_report_list()
    selected_report = st.selectbox(
        "Anh/chị muốn đánh giá báo cáo nào?",
        report_options,
        index=None, 
        placeholder="Chọn báo cáo",
        key="selected_report_name"
    )

    # -----------------------------------------------
    # BƯỚC 2: LOAD & LỌC DỮ LIỆU CẤU HÌNH
    # -----------------------------------------------
    raw_config = get_config_data()
    
    visual_items = []
    filter_items_data = []
    intro_image_link = None
    intro_image_caption = ""

    if raw_config:
        for row in raw_config:
            # Lấy thông tin từ cột
            sheet_report_name = row.get("Report Name", "").strip()
            item_type = row.get("Type", "").strip() # Cột: Visual / Filter / Template
            
            # Chỉ lấy dữ liệu khớp với báo cáo đang chọn
            if sheet_report_name == selected_report:
                lbl = row.get("Label", "")
                dsc = row.get("Description", "")
                raw_img = row.get("Image URL", "")
                
                if item_type == "Filter":
                    filter_items_data.append((lbl, dsc, raw_img))
                elif item_type == "Template":
                    intro_image_link = raw_img
                    intro_image_caption = lbl
                else:
                    visual_items.append((lbl, dsc, raw_img))

    # -----------------------------------------------
    # BƯỚC 3: HIỂN THỊ INTRO & ẢNH BÌA
    # -----------------------------------------------
    st.markdown("""
    <div class="intro-text">
        Chào anh/chị,<br>
        Mục tiêu: Xác định các biểu đồ/bộ lọc không mang lại giá trị và cải thiện hiệu năng.<br>
    </div>
    """, unsafe_allow_html=True)

    if intro_image_link:
        match = re.search(r'[/\?&](?:d|id|file/d/)=([a-zA-Z0-9_-]+)', intro_image_link)
        if match:
            file_id = match.group(1)
            download_url = f"https://drive.google.com/uc?export=view&id={file_id}"
            try:
                response = requests.get(download_url, timeout=5)
                if response.status_code == 200:
                    c1, c2, c3 = st.columns([1, 4, 1]) 
                    with c2:
                        st.image(BytesIO(response.content), caption=intro_image_caption, width='stretch')
            except: pass

    # -----------------------------------------------
    # BƯỚC 4: FORM NHẬP LIỆU
    # -----------------------------------------------
    with st.form("survey_form"):
        st.markdown('<div class="section-header">1. THÔNG TIN CHUNG</div>', unsafe_allow_html=True)
        st.write("**Username của anh/chị:**")
        
        c_user, c_domain = st.columns([2, 5])
        with c_user:
            username_input = st.text_input("User Account", key="user_name_input", label_visibility="collapsed")
        with c_domain:
            st.markdown(f"<div style='padding-top: 10px; font-size: 18px; color: #555;'>{EMAIL_DOMAIN}</div>", unsafe_allow_html=True)

        st.write("**Anh/chị thường truy cập Dashboard này khi nào?** *")
        st.radio("Tần suất truy cập", ["Hàng ngày (Vận hành)", "Hàng tuần (Báo cáo/Họp)", "Hàng tháng (Chiến lược)", "Chỉ khi có sự cố bất thường xảy ra", "Hiếm khi/Chưa bao giờ"], key="q1", index=None, label_visibility="collapsed")

        st.write("**Mục đích lớn nhất của anh/chị khi mở Dashboard là gì?** *")
        # Danh sách đáp án
        q2_options = [
            "Theo dõi tiến độ hoàn thành mục tiêu (KPIs).", 
            "Tìm kiếm nguyên nhân của một vấn đề cụ thể (Drill-down).", 
            "Lấy số liệu để xuất báo cáo/gửi cho cấp trên.", 
            "Giám sát dữ liệu thời gian thực để đưa ra hành động ngay lập tức.",
            "Khác"
        ]
        
        # 1. Dùng Multiselect thay vì Radio
        st.multiselect(
            "Mục đích truy cập", 
            q2_options, 
            key="q2_select", # Đổi key khác với cũ để tránh lỗi
            label_visibility="collapsed",
            placeholder="Chọn một hoặc nhiều mục đích..."
        )
        
        # 2. Ô nhập liệu cho mục Khác (Luôn hiện để tránh lỗi Form)
        st.text_input(
            "Chi tiết mục đích khác (Nếu chọn 'Khác')", 
            key="q2_other_text", 
            placeholder="Nếu chọn 'Khác', vui lòng nhập chi tiết tại đây..."
        )
        # RENDER VISUALS
        if visual_items:
            st.markdown('<div class="section-header">PHẦN 2: ĐÁNH GIÁ CHI TIẾT VISUAL</div>', unsafe_allow_html=True)
            st.info("💡 Di chuột vào tên thành phần (bên trái) để xem Ảnh minh họa.")
            c1, c2 = st.columns([7, 3])
            c1.markdown("**Thành phần**")
            c2.markdown("**Đánh giá & Vấn đề**")
            st.markdown("---")
            for idx, (label, desc, img_link) in enumerate(visual_items):
                render_combined_visual_row(idx, label, desc, img_link)
            st.text_area("Đề xuất của Anh/chị để cải thiện các mục visual trên *", key="q5")

        # RENDER FILTERS
        if filter_items_data:
            st.markdown('<div class="section-header">PHẦN 3. ĐÁNH GIÁ CHI TIẾT FILTER</div>', unsafe_allow_html=True)
            c1, c2 = st.columns([7, 3])
            c1.markdown("**Bộ lọc (Filter)**")
            c2.markdown("**Mức độ cần thiết**")
            st.markdown("---")
            for idx, (label, desc, img_link) in enumerate(filter_items_data):
                render_filter_row(idx, label, desc, img_link)
            st.text_area("Đề xuất của Anh/chị để cải thiện các mục filter trên *", key="q7")

        st.markdown("---")
        submitted = st.form_submit_button("GỬI KHẢO SÁT", type="primary", width='stretch')

    # -----------------------------------------------
    # BƯỚC 5: XỬ LÝ GỬI DỮ LIỆU
    # -----------------------------------------------
    if submitted:
        with st.spinner("Đang xử lý dữ liệu..."):
            try:
                # 1. Chuẩn bị dữ liệu cơ bản
                tz = pytz.timezone('Asia/Ho_Chi_Minh')
                timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                
                raw_user = st.session_state.get("user_name_input", "").strip()
                if not raw_user:
                    st.error("⚠️ Vui lòng nhập Username trước khi gửi!")
                    st.stop()
                
                # 2. TẠO DÒNG DỮ LIỆU (ROW DATA) - Cấu trúc động
                row_data = []
                
                row_data.append(timestamp)
                row_data.append(f"{raw_user}{EMAIL_DOMAIN}")
                row_data.append(selected_report) # Report Name
                row_data.append(st.session_state.get("q1", ""))
                q2_answers = st.session_state.get("q2_select", [])
                # Kiểm tra xem có chọn 'Khác' không
                if "Khác" in q2_answers:
                    # Lấy nội dung người dùng nhập tay
                    other_text = st.session_state.get("q2_other_text", "").strip()
                    
                    # Xóa chữ "Khác" khỏi danh sách để thay bằng nội dung chi tiết
                    q2_answers.remove("Khác")
                    
                    if other_text:
                        q2_answers.append(f"Khác: {other_text}")
                    else:
                        q2_answers.append("Khác (Không ghi chi tiết)")
                
                # 3. Nối tất cả thành một chuỗi (ngăn cách bằng dấu chấm phẩy)
                final_q2_string = "; ".join(q2_answers)
                row_data.append(final_q2_string)
                
                # - Data Visual
                for idx, item in enumerate(visual_items):
                    val = st.session_state.get(f"vis_rating_{idx}")
                    row_data.append(val if val else "")
                    issues = st.session_state.get(f"vis_issue_{idx}", [])
                    row_data.append(", ".join(issues) if issues else "")
                
                row_data.append(st.session_state.get("q5", ""))
                
                # - Data Filter
                for idx, item in enumerate(filter_items_data):
                    val = st.session_state.get(f"fil_rating_{idx}")
                    row_data.append(val if val else "")
                    
                row_data.append(st.session_state.get("q7", ""))
                
                # 3. KẾT NỐI SHEET VÀ GHI
                # Tạo header động
                dynamic_headers = generate_target_columns(visual_items, filter_items_data)
                
                # Tìm đúng Sheet hoặc tạo mới
                sheet = get_or_create_sheet(selected_report, dynamic_headers)
                
                # Ghi dữ liệu
                sheet.append_row(
                    row_data, 
                    value_input_option='USER_ENTERED', 
                    insert_data_option='INSERT_ROWS',
                    table_range='A1'
                )
                
                st.session_state['submitted'] = True
                st.rerun()
                
            except Exception as e:
                st.error(f"Lỗi: {e}")

