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

# --- 1. CẤU HÌNH ---
DATA_SHEET_URL = "https://docs.google.com/spreadsheets/d/1DMgxkDSp_dq7IMzEmHdGK-nypIc_PLSsmTUIwFCXqZ8/edit"
CONFIG_SHEET_URL = "https://docs.google.com/spreadsheets/d/1nNJI1oxEhgYtNCk1pdEFyIR6M4UPrfjRw1F_rljyAHM/edit" 
EMAIL_DOMAIN = "@winmart.masangroup.com"

TARGET_COLUMNS = [
    "Timestamp", 
    "Email",
    "1. Anh/chị thường truy cập Dashboard này khi nào?", 
    "2. Mục đích lớn nhất của anh/chị khi mở Dashboard là gì?",
    "3. Anh/chị vui lòng đánh giá từng thành phần visual trong dashboard [Card % Sales: Hiển thị % tăng trưởng doanh thu so với kỳ trước theo thời gian chọn.]",
    "3. Anh/chị vui lòng đánh giá từng thành phần visual trong dashboard [Text box Filter: Hiển thị liệt kê các điều kiện lọc đang được lựa chọn.]",
    "3. Anh/chị vui lòng đánh giá từng thành phần visual trong dashboard [StoreProfile.Group_Concept: Concept cửa hàng, có khả năng drill down đến: Phân vùng -> Tỉnh/TP -> Quận/Huyện -> Phường/Xã -> Mã cửa hàng_Tên cửa hàng]",
    "3. Anh/chị vui lòng đánh giá từng thành phần visual trong dashboard [StoreProfile.GĐM: Giám đốc miền, có khả năng drill down đến: Mã cửa hàng_Tên cửa hàng]",
    "3. Anh/chị vui lòng đánh giá từng thành phần visual trong dashboard [StoreProfile.GĐC: Giám đốc chuỗi, có khả năng drill down đến: Giám đốc miền -> Giám đốc vùng -> Quản lý khu vực -> Mã cửa hàng_Tên cửa hàng]",
    "3. Anh/chị vui lòng đánh giá từng thành phần visual trong dashboard [StoreProfile.Miền: Miền, có khả năng drill down đến: Tỉnh/TP -> Quận/Huyện -> Mã cửa hàng_Tên cửa hàng]",
    "3. Anh/chị vui lòng đánh giá từng thành phần visual trong dashboard [Total Sales: Tổng doanh thu theo cửa hàng trong khoảng thời gian chọn.]",
    "3. Anh/chị vui lòng đánh giá từng thành phần visual trong dashboard [#Store: Số lượng cửa hàng hoạt động trong kỳ.]",
    "3. Anh/chị vui lòng đánh giá từng thành phần visual trong dashboard [Sales per day: Doanh thu trung bình theo store trên mỗi ngày hoạt động.]",
    "3. Anh/chị vui lòng đánh giá từng thành phần visual trong dashboard [Sales per day (Vs. Previous): % Tăng trưởng doanh thu trung bình ngày so với kỳ trước.]",
    "3. Anh/chị vui lòng đánh giá từng thành phần visual trong dashboard [Bill per Day: Số hóa đơn bình quân theo store trên mỗi ngày hoạt động.]",
    "3. Anh/chị vui lòng đánh giá từng thành phần visual trong dashboard [Bill per Day (Vs. Previous): % Tăng trưởng số hóa đơn bình quân ngày so với kỳ trước.]",
    "3. Anh/chị vui lòng đánh giá từng thành phần visual trong dashboard [Bill Size: Giá trị trung bình mỗi hóa đơn bán ra (ATV).]",
    "3. Anh/chị vui lòng đánh giá từng thành phần visual trong dashboard [Bill Size (Vs. Previous): % Tăng trưởng giá trị hóa đơn so với kỳ trước.]",
    "3. Anh/chị vui lòng đánh giá từng thành phần visual trong dashboard [% Penetration: Tỷ lệ hóa đơn có chứa sản phẩm của ngành hàng (Độ thâm nhập).]",
    "3. Anh/chị vui lòng đánh giá từng thành phần visual trong dashboard [% Penetration (Vs. Previous): % Tăng trưởng tỷ lệ thâm nhập so với kỳ trước.]",
    "4. Đối với những mục visual trên, anh/chị cảm thấy vẫn còn tồn đọng vấn đề gì? (Chọn tất cả phù hợp) [Card % Sales: Hiển thị % tăng trưởng doanh thu so với kỳ trước theo thời gian chọn.]",
    "4. Đối với những mục visual trên, anh/chị cảm thấy vẫn còn tồn đọng vấn đề gì? (Chọn tất cả phù hợp) [Text box Filter: Hiển thị liệt kê các điều kiện lọc đang được lựa chọn.]",
    "4. Đối với những mục visual trên, anh/chị cảm thấy vẫn còn tồn đọng vấn đề gì? (Chọn tất cả phù hợp) [StoreProfile.Group_Concept: Concept cửa hàng, có khả năng drill down đến: Phân vùng -> Tỉnh/TP -> Quận/Huyện -> Phường/Xã -> Mã cửa hàng_Tên cửa hàng]",
    "4. Đối với những mục visual trên, anh/chị cảm thấy vẫn còn tồn đọng vấn đề gì? (Chọn tất cả phù hợp) [StoreProfile.GĐM: Giám đốc miền, có khả năng drill down đến: Mã cửa hàng_Tên cửa hàng]",
    "4. Đối với những mục visual trên, anh/chị cảm thấy vẫn còn tồn đọng vấn đề gì? (Chọn tất cả phù hợp) [StoreProfile.GĐC: Giám đốc chuỗi, có khả năng drill down đến: Giám đốc miền -> Giám đốc vùng -> Quản lý khu vực -> Mã cửa hàng_Tên cửa hàng]",
    "4. Đối với những mục visual trên, anh/chị cảm thấy vẫn còn tồn đọng vấn đề gì? (Chọn tất cả phù hợp) [StoreProfile.Miền: Miền, có khả năng drill down đến: Tỉnh/TP -> Quận/Huyện -> Mã cửa hàng_Tên cửa hàng]",
    "4. Đối với những mục visual trên, anh/chị cảm thấy vẫn còn tồn đọng vấn đề gì? (Chọn tất cả phù hợp) [Total Sales: Tổng doanh thu theo cửa hàng trong khoảng thời gian chọn.]",
    "4. Đối với những mục visual trên, anh/chị cảm thấy vẫn còn tồn đọng vấn đề gì? (Chọn tất cả phù hợp) [#Store: Số lượng cửa hàng hoạt động trong kỳ.]",
    "4. Đối với những mục visual trên, anh/chị cảm thấy vẫn còn tồn đọng vấn đề gì? (Chọn tất cả phù hợp) [Sales per day: Doanh thu trung bình theo store trên mỗi ngày hoạt động.]",
    "4. Đối với những mục visual trên, anh/chị cảm thấy vẫn còn tồn đọng vấn đề gì? (Chọn tất cả phù hợp) [Sales per day (Vs. Previous): % Tăng trưởng doanh thu trung bình ngày so với kỳ trước.]",
    "4. Đối với những mục visual trên, anh/chị cảm thấy vẫn còn tồn đọng vấn đề gì? (Chọn tất cả phù hợp) [Bill per Day: Số hóa đơn bình quân theo store trên mỗi ngày hoạt động.]",
    "4. Đối với những mục visual trên, anh/chị cảm thấy vẫn còn tồn đọng vấn đề gì? (Chọn tất cả phù hợp) [Bill per Day (Vs. Previous): % Tăng trưởng số hóa đơn bình quân ngày so với kỳ trước.]",
    "4. Đối với những mục visual trên, anh/chị cảm thấy vẫn còn tồn đọng vấn đề gì? (Chọn tất cả phù hợp) [Bill Size: Giá trị trung bình mỗi hóa đơn bán ra (ATV).]",
    "4. Đối với những mục visual trên, anh/chị cảm thấy vẫn còn tồn đọng vấn đề gì? (Chọn tất cả phù hợp) [Bill Size (Vs. Previous): % Tăng trưởng giá trị hóa đơn so với kỳ trước.]",
    "4. Đối với những mục visual trên, anh/chị cảm thấy vẫn còn tồn đọng vấn đề gì? (Chọn tất cả phù hợp) [% Penetration: Tỷ lệ hóa đơn có chứa sản phẩm của ngành hàng (Độ thâm nhập).]",
    "4. Đối với những mục visual trên, anh/chị cảm thấy vẫn còn tồn đọng vấn đề gì? (Chọn tất cả phù hợp) [% Penetration (Vs. Previous): % Tăng trưởng tỷ lệ thâm nhập so với kỳ trước.]",
    "5. Đề xuất của Anh/chị để cải thiện các mục visual trên",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Current Date: Chọn khoảng thời gian xem báo cáo hiện tại.]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Previous Date: Chọn khoảng thời gian quá khứ để so sánh.]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [LW/MTD/YTD: Chọn chế độ xem lũy kế (Tuần trước/Tháng này/Năm nay).]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Weekday/Weekend: Lọc dữ liệu riêng cho Ngày trong tuần hoặc Cuối tuần.]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Category (MCH 2, 3): Lọc theo nhóm ngành hàng MCH 2, MCH 3.]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Category (MCH 4, 5): Lọc theo nhóm ngành hàng MCH 4, MCH 5.]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Project MCH: Lọc theo các dự án ngành hàng.]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Revenue Type: Lọc theo loại hình doanh thu.]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Bill Type: Lọc theo loại hóa đơn.]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Chain: Lọc theo Chuỗi cửa hàng.]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Format: Lọc theo Mô hình cửa hàng (Format).]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Region: Lọc theo Vùng địa lý.]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [RSM / ASM: Lọc theo cấp Quản lý vùng/khu vực.]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Cohort: Lọc theo nhóm phân loại Cohort.]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Performance Tier: Lọc theo nhóm phân loại Hiệu suất cửa hàng.]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Store Project: Lọc theo các dự án cửa hàng.]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Store ID (Dropdown): Tìm và chọn một hoặc nhiều mã cửa hàng cụ thể.]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Store Input (Paste): Chức năng nhập/dán hàng loạt mã cửa hàng để lọc nhanh.]",
    "6. Anh/chị vui lòng đánh giá từng thành phần filter trong dashboard [Apply / Clear: Nút xác nhận áp dụng hoặc xóa trắng các điều kiện lọc.]",
    "7. Đề xuất của Anh/chị để cải thiện các mục filter trên"
]

def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"]) 
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

@st.cache_resource
def connect_to_data_sheet():
    try:
        client = get_gspread_client()
        sh = client.open_by_url(DATA_SHEET_URL)
        try:
            worksheet = sh.worksheet("KetQua")
        except gspread.WorksheetNotFound:
            worksheet = sh.add_worksheet(title="KetQua", rows=1000, cols=20)
        return worksheet
    except Exception as e:
        st.error(f"Lỗi kết nối File Data: {e}")
        return None

@st.cache_resource
def get_config_data():
    try:
        client = get_gspread_client()
        worksheet = client.open_by_url(CONFIG_SHEET_URL).worksheet("Config_Visual")
        return worksheet.get_all_records()
    except Exception as e:
        return []

# --- 2. CẤU HÌNH TRANG & CSS ---
st.set_page_config(page_title="Khảo sát BI Dashboard CMC", layout="wide")

st.markdown("""
<style>
    /* 1. Khung chứa chính */
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

    /* 2. Nội dung Pop-up (Container) */
    .tooltip .tooltiptext {
        visibility: hidden;
        
        /* Tự động ôm sát nội dung */
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
        
        /* Căn giữa dọc và sang phải */
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
        white-space: normal; /* Đảm bảo văn bản tự xuống dòng */
    }

    /* 3. Mũi tên chỉ sang trái */
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
    
    /* 4. Hình ảnh (Image) */
    .tooltip-img {
        /* LOGIC TỰ ĐIỀU CHỈNH KHỔ ẢNH */
        width: auto;
        height: auto;
        max-width: 100%;
        max-height: 450px; /* Chặn chiều cao ảnh dọc */
        
        display: block;
        margin: 0 auto 12px auto;
        border-radius: 6px;
        border: 1px solid #eee;
    }
    
    .section-header { font-size: 22px; font-weight: bold; margin-top: 40px; margin-bottom: 20px; color: #262730; border-bottom: 2px solid #f0f2f6; padding-bottom: 10px; }
    .small-text { font-size: 13px; color: #666; font-style: italic; }
    .thank-you-box { text-align: center; padding: 50px; background-color: #f0f8ff; border-radius: 15px; margin-top: 20px; }
    .thank-you-title { color: #2E86C1; font-size: 32px; font-weight: bold; }
    .thank-you-text { font-size: 18px; color: #555; margin-top: 15px; }
    
    /* Ẩn dòng chữ hướng dẫn mặc định của Input */
    [data-testid="InputInstructions"] { display: none; }
</style>
""", unsafe_allow_html=True)

# --- 3. LOAD DATA & IMAGE PROCESSING (BASE64) ---
NUM_VISUALS = 16 
img_placeholder = "https://via.placeholder.com/400x200?text=No+Image"

@st.cache_data(show_spinner=False)
def get_image_as_base64(drive_link):
    """
    Tải ảnh từ Google Drive và chuyển thành Base64 để hiển thị trong HTML Tooltip.
    Khắc phục triệt để lỗi 403 Forbidden của Google.
    """
    if not drive_link: return None
    
    # 1. Lấy ID ảnh
    match = re.search(r'[/\?&](?:d|id|file/d/)=([a-zA-Z0-9_-]+)', drive_link)
    if not match: return None
    file_id = match.group(1)
    
    # 2. Tải ảnh về
    url = f"https://drive.google.com/uc?export=view&id={file_id}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            # 3. Mã hóa Base64
            encoded = base64.b64encode(response.content).decode()
            return f"data:image/jpeg;base64,{encoded}"
    except:
        pass
    return None

raw_config = get_config_data()
loaded_items = []

if raw_config:
    for row in raw_config:
        lbl = row.get("Label", "")
        dsc = row.get("Description", "")
        raw_img_link = row.get("Image URL", "")
        # Lưu link gốc, việc tải sẽ làm ở lúc render để tối ưu
        loaded_items.append((lbl, dsc, raw_img_link))
else:
    loaded_items = [("Item Mẫu", "Mô tả...", "")] * 35

if len(loaded_items) >= NUM_VISUALS:
    visual_items = loaded_items[:NUM_VISUALS]
    filter_items_data = loaded_items[NUM_VISUALS:] 
else:
    visual_items = loaded_items
    filter_items_data = []

issues_list = ["Cách trình bày/biểu đồ quá phức tạp", "Số liệu thường xuyên sai lệch", "Font chữ nhỏ, màu sắc khó nhìn", "Cần số liệu này nhưng không xem được", "Khó thao tác", "Tốc độ tải quá chậm", "Không hiển thị tốt trên thiết bị của tôi"]

# --- 4. RENDER FUNCTIONS (ĐÃ SỬA SELECTBOX & BASE64) ---
def render_combined_visual_row(index, label, description, raw_link):
    # Xử lý ảnh bằng Base64 để nhúng vào HTML
    base64_img = get_image_as_base64(raw_link)
    display_src = base64_img if base64_img else img_placeholder

    col1, col2 = st.columns([7, 3])
    with col1:
        s1, s2 = st.columns([2, 5])
        with s1:
            tooltip_html = f"""
            <div class="tooltip">
                <span> {label}</span>
                <span class="tooltiptext">
                    <img src="{display_src}" class="tooltip-img" alt="Minh họa">
                    <br>{description}<br>
                </span>
            </div>
            """
            st.markdown(tooltip_html, unsafe_allow_html=True)
    with col2:
        st.markdown(f"<span class='small-text' style='color:#D35400'>Mức độ cần thiết:</span>", unsafe_allow_html=True)
        rating_options = ["Rất không cần thiết", "Không cần thiết", "Bình thường", "Cần thiết", "Rất cần thiết"]

        # SỬA: Selectbox, index=None, KHÔNG có max_selections
        st.selectbox(
            f"Rating {label}", 
            rating_options, 
            key=f"vis_rating_{index}", 
            index=None,  
            placeholder="Chọn mức độ...",
            label_visibility="collapsed"
        )
            
        st.markdown(f"<span class='small-text' style='color:#D35400'>Vấn đề tồn đọng (nếu có):</span>", unsafe_allow_html=True)
        st.multiselect(f"Issues {label}", issues_list, key=f"vis_issue_{index}", label_visibility="collapsed", placeholder="Chọn vấn đề...")
    st.markdown("<hr style='margin: 15px 0; border-top: 1px solid #f0f2f6;'>", unsafe_allow_html=True)

def render_filter_row(index, label, description, raw_link):
    base64_img = get_image_as_base64(raw_link)
    display_src = base64_img if base64_img else img_placeholder

    col1, col2 = st.columns([7, 3])
    with col1:
        s1, s2 = st.columns([2, 5])
        with s1:
            tooltip_html = f"""
            <div class="tooltip">
                <span> {label}</span>
                <span class="tooltiptext">
                    <img src="{display_src}" class="tooltip-img" alt="Minh họa">
                    <br>{description}<br>
                </span>
            </div>
            """
            st.markdown(tooltip_html, unsafe_allow_html=True)
    with col2:
        st.markdown(f"<span class='small-text' style='color:#D35400'>Mức độ cần thiết:</span>", unsafe_allow_html=True)
        rating_options = ["Rất không cần thiết", "Không cần thiết", "Bình thường", "Cần thiết", "Rất cần thiết"]
            
        # SỬA: Selectbox, sửa key thành 'fil_'
        st.selectbox(
            f"Filter Rating {label}", 
            rating_options, 
            key=f"fil_rating_{index}", 
            index=None, 
            placeholder="Chọn mức độ...",
            label_visibility="collapsed"
        )
    st.markdown("<hr style='margin: 15px 0; border-top: 1px dashed #eee;'>", unsafe_allow_html=True)

# --- 5. LOGIC CHUYỂN TRANG (SESSION STATE) ---
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
    st.title("Khảo sát nhu cầu sử dụng BI dashboard của CMC")
    st.markdown("""
    <div class="intro-text">
        Chào anh/chị,<br>
        Mục tiêu: Xác định các biểu đồ/bộ lọc không mang lại giá trị và cải thiện hiệu năng.<br>
    </div>
    """, unsafe_allow_html=True)

    INTRO_IMAGE_LINK = "https://drive.google.com/file/d/1L3qD--XLvazv9op8jGG-mPUn_qzk2oab/view?usp=drive_link"
    if INTRO_IMAGE_LINK:
        match = re.search(r'(/d/|id=)([a-zA-Z0-9_-]+)', INTRO_IMAGE_LINK)
        if match:
            file_id = match.group(2)
            download_url = f"https://drive.google.com/uc?export=view&id={file_id}"
            try:
                # Ảnh intro này dùng st.image nên dùng download_url OK
                response = requests.get(download_url)
                if response.status_code == 200:
                    c1, c2, c3 = st.columns([1, 4, 1]) 
                    with c2:
                        st.image(BytesIO(response.content), caption="RP_Sales_Daily_MCH_Store – Sales by Store", width="stretch")
            except: pass

    with st.form("survey_form"):
        st.markdown('<div class="section-header">1. THÔNG TIN CHUNG</div>', unsafe_allow_html=True)
        st.write("**Tên đăng nhập của anh/chị:**")
        
        # Ô nhập liệu Username + Đuôi Email
        c_user, c_domain = st.columns([2, 5])
        with c_user:
            username_input = st.text_input(
                "User Account", 
                key="user_name_input", 
                label_visibility="collapsed"
            )
        with c_domain:
            st.markdown(
                f"<div style='padding-top: 10px; font-size: 18px; color: #555;'>{EMAIL_DOMAIN}</div>", 
                unsafe_allow_html=True
            )

        st.write("**1. Anh/chị thường truy cập Dashboard này khi nào?** *")
        # Sửa lỗi: Thêm Label nhưng để collapsed
        st.radio("Tần suất truy cập", ["Hàng ngày (Vận hành)", "Hàng tuần (Báo cáo/Họp)", "Hàng tháng (Chiến lược)", "Chỉ khi có sự cố bất thường xảy ra", "Hiếm khi/Chưa bao giờ"], key="q1", index=None, label_visibility="collapsed")

        st.write("**2. Mục đích lớn nhất của anh/chị khi mở Dashboard là gì?** *")
        st.radio("Mục đích truy cập", ["Theo dõi tiến độ hoàn thành mục tiêu (KPIs).", "Tìm kiếm nguyên nhân của một vấn đề cụ thể (Drill-down).", "Lấy số liệu để xuất báo cáo/gửi cho cấp trên.", "Giám sát dữ liệu thời gian thực để đưa ra hành động ngay lập tức."], key="q2", index=None, label_visibility="collapsed")

        st.markdown('<div class="section-header">PHẦN 2: ĐÁNH GIÁ CHI TIẾT VISUAL</div>', unsafe_allow_html=True)
        st.info("💡 Di chuột vào tên thành phần (bên trái) để xem Ảnh minh họa.")
        
        c1, c2 = st.columns([7, 3])
        c1.markdown("**Thành phần**")
        c2.markdown("**Đánh giá & Vấn đề**")
        st.markdown("---")
        for idx, (label, desc, img_link) in enumerate(visual_items):
            render_combined_visual_row(idx, label, desc, img_link)
        st.text_area("5. Đề xuất của Anh/chị để cải thiện các mục visual trên *", key="q5")

        st.markdown('<div class="section-header">PHẦN 3. ĐÁNH GIÁ CHI TIẾT FILTER</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([7, 3])
        c1.markdown("**Bộ lọc (Filter)**")
        c2.markdown("**Mức độ cần thiết**")
        st.markdown("---")
        if not filter_items_data:
            st.info("Đang tải dữ liệu Filter...")
        else:
            for idx, (label, desc, img_link) in enumerate(filter_items_data):
                render_filter_row(idx, label, desc, img_link)
        st.text_area("7. Đề xuất của Anh/chị để cải thiện các mục filter trên *", key="q7")

        st.markdown("---")
        submitted = st.form_submit_button("GỬI KHẢO SÁT", type="primary", use_container_width=True)

    if submitted:
        with st.spinner("Đang gửi dữ liệu, vui lòng đợi trong giây lát..."):
            sheet = connect_to_data_sheet()
            if sheet:
                try:
                    tz = pytz.timezone('Asia/Ho_Chi_Minh')
                    timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                    row_data = [timestamp]
                    
                    # Ghép email
                    raw_user = st.session_state.get("user_name_input", "").strip()
                    if not raw_user:
                        st.error("⚠️ Vui lòng nhập Username trước khi gửi!")
                        st.stop()
                    full_email = f"{raw_user}{EMAIL_DOMAIN}"
                    row_data.append(full_email)

                    row_data.append(st.session_state.get("q1", ""))
                    row_data.append(st.session_state.get("q2", ""))
                    
                    # LOGIC LẤY DATA TỪ SELECTBOX (Lấy giá trị trực tiếp)
                    for idx in range(len(visual_items)):
                        # Selectbox trả về String hoặc None
                        val = st.session_state.get(f"vis_rating_{idx}")
                        row_data.append(val if val else "")

                    for idx in range(len(visual_items)):
                        issues = st.session_state.get(f"vis_issue_{idx}", [])
                        row_data.append(", ".join(issues) if issues else "")
                    
                    row_data.append(st.session_state.get("q5", ""))
                    
                    for idx in range(len(filter_items_data)):
                        # Selectbox Filter
                        val = st.session_state.get(f"fil_rating_{idx}")
                        row_data.append(val if val else "")
                    
                    row_data.append(st.session_state.get("q7", ""))

                    if len(sheet.get_all_values()) == 0:
                        sheet.append_row(TARGET_COLUMNS)
                    
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

