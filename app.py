"""
智扫通机器人智能客服 Web 界面

采用 IDE 风格三栏式布局：
- 左侧 (Sidebar): 用户信息 + 会话列表
- 中间 (Stage): 对话流 + 思考链可视化
- 右侧 (Inspector): 查看/编辑文件

UI风格: 浅色 Apple 风格 (Frosted Glass)
"""

import os
import time
from datetime import datetime

import streamlit as st
from agent.react_deep_agent import ReactDeepAgent
from utils.user_context import get_user_context
from utils import memory_manager


st.set_page_config(
    page_title="智扫通智能客服",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
<style>
    /* 浅色 Apple 风格 */
    :root {
        --bg-color: #fafafa;
        --sidebar-bg: rgba(255, 255, 255, 0.8);
        --accent-color: #007AFF;
        --text-primary: #1d1d1f;
        --text-secondary: #86868b;
        --border-color: #e5e5e5;
        --card-bg: rgba(255, 255, 255, 0.9);
    }
    
    /* 主背景 */
    .stApp {
        background-color: #fafafa;
    }
    
    /* 侧边栏 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.9) 0%, rgba(245,245,247,0.9) 100%);
        backdrop-filter: blur(20px);
        border-right: 1px solid #e5e5e5;
    }
    
    /* 卡片样式 */
    .stButton > button {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid #e5e5e5;
        border-radius: 10px;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: rgba(0, 122, 255, 0.1);
        border-color: #007AFF;
    }
    
    /* 输入框 */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 8px;
        border: 1px solid #e5e5e5;
    }
    
    /* 聊天消息 */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 16px;
        margin: 8px 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        border: 1px solid #e5e5e5;
    }
    
    .stChatMessageContent {
        color: #1d1d1f;
    }
    
    /* 用户消息 */
    div[data-testid="stChatMessage-user"] {
        background: rgba(0, 122, 255, 0.1);
        border-color: rgba(0, 122, 255, 0.3);
    }
    
    /* 助手消息 */
    div[data-testid="stChatMessage-assistant"] {
        background: rgba(255, 255, 255, 0.95);
    }
    
    /* 标题 */
    h1, h2, h3 {
        color: #1d1d1f;
        font-weight: 600;
    }
    
    /* 分割线 */
    .stDivider {
        border-color: #e5e5e5;
    }
    
    /* 底部状态栏 */
    .footer-bar {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 40px;
        background: linear-gradient(180deg, rgba(255,255,255,0.95) 0%, rgba(245,245,247,0.95) 100%);
        backdrop-filter: blur(20px);
        border-top: 1px solid #e5e5e5;
        display: flex;
        align-items: center;
        padding: 0 20px;
        font-size: 13px;
        color: #86868b;
        z-index: 100;
    }
    
    /* 文本区域 */
    .stTextArea textarea {
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid #e5e5e5;
        border-radius: 8px;
        color: #1d1d1f;
    }
    
    /* 展开框 */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 8px;
        border: 1px solid #e5e5e5;
    }
    
    /* 滚动条美化 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #a1a1a1;
    }
</style>
""",
    unsafe_allow_html=True,
)


user_context = get_user_context()


def init_session_state():
    """初始化 Session State"""
    if "agent" not in st.session_state:
        st.session_state["agent"] = ReactDeepAgent()

    if "message" not in st.session_state:
        st.session_state["message"] = []

    if "thought_chain" not in st.session_state:
        st.session_state["thought_chain"] = []

    if "thread_id" not in st.session_state:
        st.session_state["thread_id"] = "thread_id"

    if "session_id" not in st.session_state:
        st.session_state["session_id"] = None

    if "user_confirmed" not in st.session_state:
        st.session_state["user_confirmed"] = False

    if "inspector_file" not in st.session_state:
        st.session_state["inspector_file"] = "MEMORY.md"


def render_left_panel():
    """渲染左侧面板 - 用户信息 + 会话列表"""
    with st.sidebar:
        st.markdown("### 👤 用户信息")

        if not st.session_state.get("user_confirmed", False):
            user_id = st.text_input(
                "用户ID", placeholder="请输入用户ID", key="user_id_input"
            )

            provinces = [
                "请选择省份",
                "北京",
                "上海",
                "天津",
                "重庆",
                "广东",
                "浙江",
                "江苏",
                "四川",
                "湖北",
                "湖南",
                "山东",
                "福建",
                "安徽",
                "河北",
                "河南",
                "陕西",
                "辽宁",
                "吉林",
                "黑龙江",
                "江西",
                "云南",
                "山西",
                "广西",
                "贵州",
                "甘肃",
                "海南",
                "宁夏",
                "青海",
                "新疆",
                "西藏",
                "内蒙古",
                "香港",
                "澳门",
                "台湾",
            ]
            province = st.selectbox("省份", provinces, index=0, key="province_select")
            city = st.text_input("城市", placeholder="如：杭州、深圳", key="city_input")
            district = st.text_input(
                "区县（如有）", placeholder="如：西湖区", key="district_input"
            )

            if st.button("✅ 确认信息", use_container_width=True):
                if user_id and province != "请选择省份" and city:
                    user_context.set_user_info(user_id, province, city, district)
                    st.session_state["user_confirmed"] = True

                    sessions = memory_manager.list_user_sessions(user_id)
                    if sessions:
                        st.session_state["session_id"] = sessions[0]["session_id"]
                        st.session_state["thread_id"] = sessions[0]["session_id"]
                        st.session_state["message"] = memory_manager.load_session(
                            user_id, sessions[0]["session_id"]
                        )
                    else:
                        new_session_id = memory_manager.create_new_session(user_id)
                        st.session_state["session_id"] = new_session_id
                        st.session_state["thread_id"] = new_session_id
                        st.session_state["message"] = []
                    st.rerun()
                else:
                    st.error("请填写完整信息")
        else:
            user_id = user_context.get_user_id()
            st.success(f"✅ 用户ID: **{user_id}**")
            st.info(f"📍 {user_context.get_user_location()}")

            if st.button("✏️ 修改信息", use_container_width=True):
                user_context.clear()
                st.session_state["user_confirmed"] = False
                st.session_state["session_id"] = None
                st.session_state["message"] = []
                st.rerun()

        st.markdown("---")
        st.markdown("### 💬 会话列表")

        if st.session_state.get("user_confirmed"):
            user_id = user_context.get_user_id()
            sessions = memory_manager.list_user_sessions(user_id)

            if st.button("➕ 新建会话", use_container_width=True):
                new_session_id = memory_manager.create_new_session(user_id)
                st.session_state["session_id"] = new_session_id
                st.session_state["thread_id"] = new_session_id
                st.session_state["message"] = []
                st.rerun()

            st.markdown("---")

            for session in sessions:
                is_active = st.session_state.get("session_id") == session["session_id"]

                col1, col2 = st.columns([4, 1])
                with col1:
                    btn_label = f"📝 {session['title'][:18]}..."
                    if st.button(
                        btn_label,
                        key=f"session_{session['session_id']}",
                        use_container_width=True,
                    ):
                        st.session_state["session_id"] = session["session_id"]
                        st.session_state["thread_id"] = session["session_id"]
                        st.session_state["message"] = memory_manager.load_session(
                            user_id, session["session_id"]
                        )
                        st.rerun()
                with col2:
                    if is_active:
                        st.caption("✅")
                    if st.button("🗑️", key=f"del_{session['session_id']}"):
                        memory_manager.delete_session(user_id, session["session_id"])
                        remaining = memory_manager.list_user_sessions(user_id)
                        if remaining:
                            st.session_state["session_id"] = remaining[0]["session_id"]
                            st.session_state["thread_id"] = remaining[0]["session_id"]
                            st.session_state["message"] = memory_manager.load_session(
                                user_id, remaining[0]["session_id"]
                            )
                        else:
                            new_session_id = memory_manager.create_new_session(user_id)
                            st.session_state["session_id"] = new_session_id
                            st.session_state["thread_id"] = new_session_id
                            st.session_state["message"] = []
                        st.rerun()

                st.caption(f"🕐 {session['updated_at']}")


def render_center_panel():
    """渲染中间面板 - 对话流"""
    st.markdown("### 💬 对话")

    messages = st.session_state.get("message", [])

    with st.container():
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            col1, col2, col3 = st.columns([1, 8, 1])
            with col2:
                if role == "user":
                    st.chat_message("user").write(content)
                elif role == "assistant":
                    st.chat_message("assistant").write(content)
                elif role == "thought":
                    with st.expander("🤔 思考过程"):
                        st.markdown(content)


def save_current_session():
    """保存当前会话"""
    if st.session_state.get("user_confirmed") and st.session_state.get("session_id"):
        user_id = user_context.get_user_id()
        session_id = st.session_state["session_id"]
        messages = st.session_state.get("message", [])
        if messages:
            memory_manager.save_session(user_id, session_id, messages)


def main():
    """主函数"""
    st.markdown("# 🤖 智扫通智能客服")
    st.markdown("---")

    init_session_state()

    col_left, col_center = st.columns([1, 4], gap="medium")

    with col_left:
        render_left_panel()

    with col_center:
        render_center_panel()

        prompt = st.chat_input("请输入您的问题...")

        if prompt:
            save_current_session()

            st.chat_message("user").write(prompt)
            st.session_state["message"].append({"role": "user", "content": prompt})

            response_messages = []
            with st.spinner("🤔 智能客服思考中..."):
                res_stream = st.session_state["agent"].execute_stream(
                    query=prompt,
                    thread_id=st.session_state["thread_id"],
                )

                def capture(generator, cache_list):
                    for chunk in generator:
                        cache_list.append(chunk)
                        for char in chunk:
                            time.sleep(0.01)
                            yield char

                st.chat_message("assistant").write_stream(
                    capture(res_stream, response_messages)
                )

                st.session_state["message"].append(
                    {"role": "assistant", "content": response_messages[-1]}
                )

                save_current_session()

            st.rerun()

    current_date = datetime.now().strftime("%Y-%m-%d")
    st.markdown(
        f"""
    <div class="footer-bar">
        📅 {current_date} | 🤖 智扫通智能客服
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
