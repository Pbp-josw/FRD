import streamlit as st
from openai import OpenAI

# ------------------------------------------------------------------------------
# 1. 페이지 설정 및 세션 상태 초기화
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="AI 챗봇 서비스",
    page_icon="🤖",
    layout="wide"
)

# 세션 상태(변수) 선언
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "is_connected" not in st.session_state:
    st.session_state.is_connected = False

if "status_message" not in st.session_state:
    st.session_state.status_message = "왼쪽 사이드바에서 API 키를 입력하고 [연동 확인] 버튼을 눌러주세요."

# ------------------------------------------------------------------------------
# 2. API 키 실시간 검증 함수
# ------------------------------------------------------------------------------
def check_api_key(key: str):
    clean_key = key.strip()
    
    if not clean_key:
        return False, "API 키가 입력되지 않았습니다."
    
    if not (clean_key.startswith("sk-") or clean_key.startswith("sk-proj-")):
        return False, "올바르지 않은 키 형식입니다 ('sk-' 또는 'sk-proj-'로 시작해야 함)."

    try:
        # OpenAI 서버에 실제 작동 여부 확인 요청
        test_client = OpenAI(api_key=clean_key)
        test_client.models.list()
        return True, "OpenAI 서버와 정상적으로 연결되었습니다!"
    except Exception as e:
        err_str = str(e)
        if "Incorrect API key" in err_str or "invalid_api_key" in err_str:
            return False, "유효하지 않은 API 키입니다. 키를 다시 확인해 주세요."
        elif "quota" in err_str.lower() or "insufficient_quota" in err_str.lower():
            return False, "❌ 계정 잔액(Credit) 부족: OpenAI 사이트에서 충전이 필요합니다."
        else:
            return False, f"연동 실패 원인: {err_str}"

# ------------------------------------------------------------------------------
# 3. 사이드바 - API 키 입력 & [연동 확인] 버튼
# ------------------------------------------------------------------------------
st.sidebar.title("⚙️ API 설정")

input_key = st.sidebar.text_input(
    "OpenAI API Key 입력",
    type="password",
    value=st.session_state.api_key,
    placeholder="sk-...",
    help="https://platform.openai.com/api-keys 에서 발급받은 키"
)

# 명시적인 버튼 클릭으로 즉시 검증 처리
if st.sidebar.button("🔌 API 키 연동 확인 및 적용", use_container_width=True):
    if input_key:
        with st.sidebar.spinner("OpenAI 서버에 연결 확인 중..."):
            success, msg = check_api_key(input_key)
            st.session_state.is_connected = success
            st.session_state.status_message = msg
            if success:
                st.session_state.api_key = input_key.strip()
    else:
        st.session_state.is_connected = False
        st.session_state.status_message = "API 키를 입력창에 넣고 버튼을 눌러주세요."

st.sidebar.markdown("---")
st.sidebar.subheader("📡 사이드바 연동 상태")

# 사이드바 연동 상태 표시
if st.session_state.is_connected:
    st.sidebar.success(f"🟢 **연동 완료**\n\n{st.session_state.status_message}")
else:
    st.sidebar.error(f"🔴 **연동 안 됨**\n\n{st.session_state.status_message}")

# ------------------------------------------------------------------------------
# 4. 메인 화면 - 연동 상태 대시보드 배너 & 챗봇 인터페이스
# ------------------------------------------------------------------------------
st.title("🤖 OpenAI AI 챗봇")

# [핵심] 메인 화면 최상단 연동 상태 안내 알림창
if st.session_state.is_connected:
    st.success(f"✅ **시스템 상태:** {st.session_state.status_message}")
else:
    st.warning(f"⚠️ **시스템 상태:** {st.session_state.status_message}")

st.divider()

# 기존 대화 내역 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 메시지 입력창 및 질문 처리
if prompt := st.chat_input("질문을 입력하세요..."):
    # API 연결 안 된 경우 차단
    if not st.session_state.is_connected:
        st.error("❌ API 키가 연동되지 않았습니다. 사이드바에 키를 넣고 [API 키 연동 확인] 버튼을 눌러주세요!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                client = OpenAI(api_key=st.session_state.api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ]
                )
                full_response = response.choices[0].message.content
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                message_placeholder.error(f"⚠️ 답변 생성 중 오류 발생: {str(e)}")
