import streamlit as st
from anthropic import Anthropic

# ------------------------------------------------------------------------------
# 1. 페이지 설정 및 세션 상태 초기화
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Claude AI 챗봇",
    page_icon="🧠",
    layout="wide"
)

# 세션 상태 변수 생성
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "is_connected" not in st.session_state:
    st.session_state.is_connected = False

if "status_message" not in st.session_state:
    st.session_state.status_message = "왼쪽 사이드바에서 Claude API 키를 입력하고 [연동 확인] 버튼을 눌러주세요."

# ------------------------------------------------------------------------------
# 2. Claude API 키 실시간 검증 함수
# ------------------------------------------------------------------------------
def check_claude_api_key(key: str):
    clean_key = key.strip()
    
    if not clean_key:
        return False, "API 키가 입력되지 않았습니다."
    
    if not clean_key.startswith("sk-ant-"):
        return False, "올바르지 않은 Claude API 키 형식입니다 ('sk-ant-'로 시작해야 함)."

    try:
        # Anthropic 서버 테스트 핑 (가장 적은 토큰 호출)
        test_client = Anthropic(api_key=clean_key)
        test_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=5,
            messages=[{"role": "user", "content": "hi"}]
        )
        return True, "Anthropic (Claude) 서버와 성공적으로 연결되었습니다!"
    except Exception as e:
        err_str = str(e)
        if "authentication_error" in err_str or "invalid x-api-key" in err_str.lower():
            return False, "유효하지 않은 API 키입니다. 키를 다시 확인해 주세요."
        elif "credit" in err_str.lower() or "balance" in err_str.lower():
            return False, "❌ 계정 잔액(Credit) 부족: Anthropic Console에서 충전이 필요합니다."
        else:
            return False, f"연동 실패 원인: {err_str}"

# ------------------------------------------------------------------------------
# 3. 사이드바 - API 키 입력 & [연동 확인] 버튼
# ------------------------------------------------------------------------------
st.sidebar.title("⚙️ Claude API 설정")

input_key = st.sidebar.text_input(
    "Claude API Key 입력",
    type="password",
    value=st.session_state.api_key,
    placeholder="sk-ant-...",
    help="https://console.anthropic.com/ 에서 발급받은 API 키를 입력하세요."
)

if st.sidebar.button("🔌 API 키 연동 확인 및 적용", use_container_width=True):
    if input_key:
        with st.sidebar.spinner("Anthropic 서버 연결 확인 중..."):
            success, msg = check_claude_api_key(input_key)
            st.session_state.is_connected = success
            st.session_state.status_message = msg
            if success:
                st.session_state.api_key = input_key.strip()
    else:
        st.session_state.is_connected = False
        st.session_state.status_message = "API 키를 입력창에 넣고 버튼을 눌러주세요."

st.sidebar.markdown("---")
st.sidebar.subheader("📡 사이드바 연동 상태")

if st.session_state.is_connected:
    st.sidebar.success(f"🟢 **연동 완료**\n\n{st.session_state.status_message}")
else:
    st.sidebar.error(f"🔴 **연동 안 됨**\n\n{st.session_state.status_message}")

# ------------------------------------------------------------------------------
# 4. 메인 화면 - 연동 상태 대시보드 배너 & 챗봇 인터페이스
# ------------------------------------------------------------------------------
st.title("🧠 Claude AI 챗봇")

if st.session_state.is_connected:
    st.success(f"✅ **시스템 상태:** {st.session_state.status_message}")
else:
    st.warning(f"⚠️ **시스템 상태:** {st.session_state.status_message}")

st.divider()

# 대화 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 메시지 입력창 및 질문 처리
if prompt := st.chat_input("Claude에게 질문을 입력하세요..."):
    if not st.session_state.is_connected:
        st.error("❌ API 키가 연동되지 않았습니다. 사이드바에 'sk-ant-' 키를 넣고 [API 키 연동 확인] 버튼을 눌러주세요!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                client = Anthropic(api_key=st.session_state.api_key)
                
                # Claude 메세지 생성 API 호출
                response = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=1024,
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ]
                )
                full_response = response.content[0].text
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                message_placeholder.error(f"⚠️ 답변 생성 중 오류 발생: {str(e)}")
