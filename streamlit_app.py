# app.py
import streamlit as st
import boto3
import json
import time
from PIL import Image
import pandas as pd
from datetime import datetime
import io
import base64
import requests

# 页面配置
st.set_page_config(
    page_title="Bird Tagging System",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# AWS配置
AWS_CONFIG = {
    'region': 'us-east-1',
    'cognito': {
        'user_pool_id': 'us-east-1_XXXXXXXXX',
        'app_client_id': 'xxxxxxxxxxxxxxxxxx',
        'domain': 'your-app-name'
    },
    'api_gateway': {
        'base_url': 'https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/dev'
    },
    's3': {
        'bucket_name': 'your-bird-bucket'
    }
}

# 初始化session state
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_name' not in st.session_state:
        st.session_state.user_name = ''
    if 'upload_results' not in st.session_state:
        st.session_state.upload_results = []
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []

# 认证函数
def show_login_page():
    st.title("🕊️ Bird Tagging System")
    st.markdown("### Automatically identify and tag bird species using AI technology")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        st.markdown("#### Please sign in to continue")
        
        # 模拟登录按钮
        if st.button("🔑 Sign In with AWS Cognito", type="primary", use_container_width=True):
            # 在实际项目中，这里会重定向到Cognito
            with st.spinner("Redirecting to AWS Cognito..."):
                time.sleep(2)
                # 模拟登录成功
                st.session_state.authenticated = True
                st.session_state.user_name = "Student User"
                st.rerun()
        
        st.markdown("---")
        st.info("📝 In a real application, this would redirect to AWS Cognito for authentication.")

# 主应用界面
def show_main_app():
    # 顶部标题栏
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🕊️ Bird Tagging System")
        st.markdown(f"Welcome back, **{st.session_state.user_name}**!")
    
    with col2:
        if st.button("🚪 Logout", type="secondary"):
            st.session_state.authenticated = False
            st.session_state.user_name = ''
            st.session_state.upload_results = []
            st.session_state.search_results = []
            st.rerun()
    
    st.markdown("---")
    
    # 创建三列布局
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # 上传区域
    with col1:
        st.header("📤 Upload Files")
        uploaded_files = st.file_uploader(
            "Choose bird files",
            type=['jpg', 'jpeg', 'png', 'mp4', 'wav', 'mp3'],
            accept_multiple_files=True,
            help="Upload images, videos, or audio files of birds"
        )
        
        if uploaded_files:
            if st.button("🔍 Process Files", type="primary"):
                process_uploaded_files(uploaded_files)
    
    # 搜索区域
    with col2:
        st.header("🔍 Search Files")
        
        # 基本搜索
        search_query = st.text_input("Search by species name", placeholder="e.g., crow, pigeon")
        
        # 高级筛选
        with st.expander("🔧 Advanced Filters"):
            file_type_filter = st.selectbox("File Type", ["All", "Images", "Videos", "Audio"])
            confidence_filter = st.selectbox(
                "Confidence Level", 
                ["Any", "High (90%+)", "Medium (70%+)", "Low (50%+)"]
            )
        
        if st.button("🔍 Search", type="primary"):
            search_files(search_query, file_type_filter, confidence_filter)
        
        if st.button("🗑️ Clear Search"):
            st.session_state.search_results = []
            st.rerun()
    
    # 统计区域
    with col3:
        st.header("📊 Statistics")
        show_statistics()
        
        if st.button("📈 Detailed Stats"):
            show_detailed_statistics()
    
    st.markdown("---")
    
    # 结果显示区域
    st.header("📋 Results")
    
    # 标签页选择
    tab1, tab2 = st.tabs(["📤 Upload Results", "🔍 Search Results"])
    
    with tab1:
        show_upload_results()
    
    with tab2:
        show_search_results()

# 处理上传文件
def process_uploaded_files(uploaded_files):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        # 更新进度
        progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(progress)
        status_text.text(f"Processing {uploaded_file.name}...")
        
        # 模拟AI处理
        time.sleep(1)

        # Getting pre-signed URL
        # 获取预签名的 URL
        try:
            file_name = uploaded_file.name
            file_type = uploaded_file.type

            # Requesting pre-signed URL
            api_url = "https://3dw1wpo1ra.execute-api.us-east-1.amazonaws.com/production/upload"
            response = requests.post(
                api_url,
                json={"fileName": file_name, "fileType": file_type}
            )

            if response.status_code != 200:
                st.error("Failed to get pre-signed URL")
            else:
                upload_url = response.json()["uploadUrl"]

                # Upload file to S3 Bucket
                s3_response = requests.put(
                    upload_url,
                    data=uploaded_file.getvalue(),
                    headers={"Content-Type": file_type}
                )

                if s3_response.status_code == 200:
                    st.success("File uploaded to S3!")
                else:
                    st.error(f"Upload failed with status: {s3_response.status_code}")

        except Exception as e:
            st.error(f"An error occurred: {e}")
        
        # 生成模拟结果
        result = simulate_ai_detection(uploaded_file)
        results.append(result)
    
    # 存储结果
    st.session_state.upload_results.extend(results)
    
    # 完成
    progress_bar.progress(1.0)
    status_text.text("✅ Processing complete!")
    
    st.success(f"Successfully processed {len(uploaded_files)} file(s)!")
    time.sleep(1)
    st.rerun()

# 模拟AI检测
def simulate_ai_detection(uploaded_file):
    # 模拟鸟类species
    species_list = ['Crow', 'Pigeon', 'Sparrow', 'Robin', 'Cardinal', 'Blue Jay', 'Eagle', 'Owl']
    detected_species = species_list[hash(uploaded_file.name) % len(species_list)]
    
    # 模拟confidence
    confidence = 0.75 + (hash(uploaded_file.name) % 25) / 100
    
    # 模拟count
    count = (hash(uploaded_file.name) % 3) + 1
    
    return {
        'file_name': uploaded_file.name,
        'file_type': uploaded_file.type,
        'file_size': uploaded_file.size,
        'species': detected_species,
        'confidence': confidence,
        'count': count,
        'timestamp': datetime.now(),
        'file_data': uploaded_file.read()  # 存储文件数据用于预览
    }

# 搜索文件
def search_files(query, file_type_filter, confidence_filter):
    if not query.strip():
        st.warning("Please enter a search term")
        return
    
    with st.spinner("Searching..."):
        time.sleep(1)
        
        # 在上传结果中搜索
        search_results = []
        for result in st.session_state.upload_results:
            if query.lower() in result['species'].lower():
                search_results.append(result)
        
        # 添加模拟数据库结果
        mock_results = generate_mock_search_results(query)
        search_results.extend(mock_results)
        
        # 应用筛选
        if file_type_filter != "All":
            if file_type_filter == "Images":
                search_results = [r for r in search_results if r['file_type'].startswith('image/')]
            elif file_type_filter == "Videos":
                search_results = [r for r in search_results if r['file_type'].startswith('video/')]
            elif file_type_filter == "Audio":
                search_results = [r for r in search_results if r['file_type'].startswith('audio/')]
        
        if confidence_filter != "Any":
            confidence_map = {
                "High (90%+)": 0.9,
                "Medium (70%+)": 0.7,
                "Low (50%+)": 0.5
            }
            min_confidence = confidence_map[confidence_filter]
            search_results = [r for r in search_results if r['confidence'] >= min_confidence]
        
        st.session_state.search_results = search_results
        
    st.success(f"Found {len(search_results)} result(s) for '{query}'")

# 生成模拟搜索结果
def generate_mock_search_results(query):
    mock_database = [
        {'file_name': 'crow_flock.jpg', 'species': 'Crow', 'confidence': 0.95, 'count': 3, 'file_type': 'image/jpeg'},
        {'file_name': 'pigeon_park.mp4', 'species': 'Pigeon', 'confidence': 0.87, 'count': 2, 'file_type': 'video/mp4'},
        {'file_name': 'sparrow_song.wav', 'species': 'Sparrow', 'confidence': 0.92, 'count': 1, 'file_type': 'audio/wav'},
        {'file_name': 'robin_nest.jpg', 'species': 'Robin', 'confidence': 0.88, 'count': 1, 'file_type': 'image/jpeg'},
        {'file_name': 'eagle_soar.mp4', 'species': 'Eagle', 'confidence': 0.94, 'count': 1, 'file_type': 'video/mp4'}
    ]
    
    results = []
    for item in mock_database:
        if query.lower() in item['species'].lower():
            results.append({
                **item,
                'timestamp': datetime.now(),
                'file_data': None  # 模拟数据无文件内容
            })
    
    return results

# 显示上传结果
def show_upload_results():
    if not st.session_state.upload_results:
        st.info("📝 Upload files to see identification results here")
        return
    
    st.subheader(f"📤 {len(st.session_state.upload_results)} Upload Result(s)")
    
    for i, result in enumerate(st.session_state.upload_results):
        with st.expander(f"🔍 {result['file_name']} - {result['species']} ({result['confidence']:.1%})"):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # 显示文件预览
                if result['file_type'].startswith('image/') and result.get('file_data'):
                    try:
                        image = Image.open(io.BytesIO(result['file_data']))
                        st.image(image, caption=result['file_name'], use_column_width=True)
                    except:
                        st.info("📷 Image preview not available")
                else:
                    st.info(f"📁 {get_file_type_emoji(result['file_type'])} {result['file_type']}")
            
            with col2:
                st.markdown(f"**Species:** {result['species']}")
                st.markdown(f"**Confidence:** {result['confidence']:.1%}")
                st.markdown(f"**Count:** {result['count']} detected")
                st.markdown(f"**File Size:** {format_file_size(result['file_size'])}")
                st.markdown(f"**Uploaded:** {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button(f"👁️ View", key=f"view_{i}"):
                        st.info("File preview feature")
                with col_btn2:
                    if st.button(f"📤 Share", key=f"share_{i}"):
                        st.info("Share feature coming soon!")

# 显示搜索结果
def show_search_results():
    if not st.session_state.search_results:
        st.info("🔍 Use the search function to find files")
        return
    
    st.subheader(f"🔍 {len(st.session_state.search_results)} Search Result(s)")
    
    # 创建表格显示
    df_data = []
    for result in st.session_state.search_results:
        df_data.append({
            'File Name': result['file_name'],
            'Species': result['species'],
            'Confidence': f"{result['confidence']:.1%}",
            'Count': result['count'],
            'Type': get_file_type_display(result['file_type']),
            'Timestamp': result['timestamp'].strftime('%Y-%m-%d %H:%M') if result.get('timestamp') else 'N/A'
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True)
    
    # 详细视图
    st.subheader("📋 Detailed View")
    for i, result in enumerate(st.session_state.search_results):
        with st.expander(f"📁 {result['file_name']}"):
            col1, col2 = st.columns([1, 1])
            with col1:
                st.metric("Species", result['species'])
                st.metric("Confidence", f"{result['confidence']:.1%}")
            with col2:
                st.metric("Count", result['count'])
                st.metric("File Type", get_file_type_display(result['file_type']))

# 显示统计信息
def show_statistics():
    total_files = len(st.session_state.upload_results)
    
    if total_files == 0:
        st.info("📊 Upload files to see statistics")
        return
    
    # 基本统计
    species_count = {}
    total_detections = 0
    high_confidence_count = 0
    
    for result in st.session_state.upload_results:
        species = result['species']
        species_count[species] = species_count.get(species, 0) + result['count']
        total_detections += result['count']
        
        if result['confidence'] >= 0.9:
            high_confidence_count += 1
    
    # 显示指标
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Files", total_files)
        st.metric("Total Detections", total_detections)
    
    with col2:
        st.metric("Unique Species", len(species_count))
        st.metric("High Confidence", f"{high_confidence_count}/{total_files}")
    
    # 最常见的species
    if species_count:
        most_common = max(species_count.items(), key=lambda x: x[1])
        st.metric("Most Common", f"{most_common[0]} ({most_common[1]})")

# 显示详细统计
def show_detailed_statistics():
    st.subheader("📊 Detailed Statistics")
    
    if not st.session_state.upload_results:
        st.warning("No data available for statistics")
        return
    
    # Species分布图表
    species_data = {}
    confidence_data = []
    file_type_data = {}
    
    for result in st.session_state.upload_results:
        # Species统计
        species = result['species']
        species_data[species] = species_data.get(species, 0) + result['count']
        
        # Confidence分布
        confidence_data.append(result['confidence'])
        
        # 文件类型统计
        file_type = get_file_type_display(result['file_type'])
        file_type_data[file_type] = file_type_data.get(file_type, 0) + 1
    
    # 创建图表
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🦅 Species Distribution")
        if species_data:
            species_df = pd.DataFrame(list(species_data.items()), columns=['Species', 'Count'])
            st.bar_chart(species_df.set_index('Species'))
    
    with col2:
        st.subheader("📁 File Types")
        if file_type_data:
            file_type_df = pd.DataFrame(list(file_type_data.items()), columns=['Type', 'Count'])
            st.bar_chart(file_type_df.set_index('Type'))
    
    # Confidence分布
    st.subheader("🎯 Confidence Distribution")
    if confidence_data:
        confidence_df = pd.DataFrame({'Confidence': confidence_data})
        st.histogram(confidence_df['Confidence'], bins=20)
    
    # 导出数据
    if st.button("📥 Download Report"):
        report_data = {
            'summary': {
                'total_files': len(st.session_state.upload_results),
                'total_detections': sum(r['count'] for r in st.session_state.upload_results),
                'unique_species': len(species_data),
                'generation_time': datetime.now().isoformat()
            },
            'species_distribution': species_data,
            'file_types': file_type_data,
            'detailed_results': [
                {
                    'file_name': r['file_name'],
                    'species': r['species'],
                    'confidence': r['confidence'],
                    'count': r['count'],
                    'timestamp': r['timestamp'].isoformat()
                }
                for r in st.session_state.upload_results
            ]
        }
        
        st.download_button(
            label="📥 Download JSON Report",
            data=json.dumps(report_data, indent=2),
            file_name=f"bird_tagging_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

# 工具函数
def get_file_type_emoji(file_type):
    if file_type.startswith('image/'):
        return '🖼️'
    elif file_type.startswith('video/'):
        return '🎥'
    elif file_type.startswith('audio/'):
        return '🎵'
    else:
        return '📁'

def get_file_type_display(file_type):
    if file_type.startswith('image/'):
        return 'Image'
    elif file_type.startswith('video/'):
        return 'Video'
    elif file_type.startswith('audio/'):
        return 'Audio'
    else:
        return 'Unknown'

def format_file_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} TB"

# 主函数
def main():
    init_session_state()
    
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_main_app()

if __name__ == "__main__":
    main()