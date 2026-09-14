import streamlit as st
from openai import OpenAI

# ------------------------------------------------------------------------------
# 1. 페이지 기본 설정
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="AI 챗봇 서비스",
    page_icon="🤖",
    layout="wide"
)

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_status" not in st.session_state:
    st.session_state.api_status = {"valid": False, "message": "API 키가 입력되지 않았습니다."}

# ------------------------------------------------------------------------------
# 2. API 키 검증 함수 (유효성 확인)
# ------------------------------------------------------------------------------
def verify_openai_api_key(api_key: str):
    """OpenAI 서버에 경량 요청을 보내 API 키의 유효성을 검증합니다."""
    if not api_key:
        return False, "API 키를 입력해 주세요."
    
    if not api_key.startswith("sk-"):
        return False, "올바르지 않은 API 키 형식입니다 (sk-로 시작해야 함)."

    try:
        # 테스트용 임시 클라이언트 생성
        test_client = OpenAI(api_key=api_key)
        # 가장 가벼운 모델 목록 조회 요청으로 키 유효성 확인
        test_client.models.list()
        return True, "API 키가 성공적으로 연동되었습니다!"
    except Exception as e:
        error_msg = str(e)
        if "Incorrect API key" in error_msg or "invalid_api_key" in error_msg:
            return False, "유효하지 않은 API 키입니다. 키를 다시 확인해 주세요."
        elif "quota" in error_msg.lower():
            return False, "API 키의 계정 잔액/한도가 초과되었습니다."
        else:
            return False, f"연동 실패: {error_msg}"

# ------------------------------------------------------------------------------
# 3. 사이드바 - API 키 입력 및 연동 상태 표기
# ------------------------------------------------------------------------------
st.sidebar.title("⚙️ 설정")

api_key = st.sidebar.text_input(
    "OpenAI API Key 입력",
    type="password",
    placeholder="sk-...",
    help="https://platform.openai.com/api-keys 에서 발급받은 키를 입력하세요."
)

# API 키 입력 상태 감지 및 검증 수행
if api_key:
    with st.sidebar.spinner("API 키 연동 확인 중..."):
        is_valid, msg = verify_openai_api_key(api_key)
        st.session_state.api_status = {"valid": is_valid, "message": msg}
else:
    st.session_state.api_status = {"valid": False, "message": "API 키가 입력되지 않았습니다."}

# 사이드바 연동 상태 카드
st.sidebar.markdown("---")
st.sidebar.subheader("📡 사이드바연동 상태")
if st.session_state.api_status["valid"]:
    st.sidebar.success(f"🟢 **연동 완료**\n\n{st.session_state.api_status['message']}")
else:
    st.sidebar.error(f"🔴 **연동 안 됨**\n\n{st.session_state.api_status['message']}")

# ------------------------------------------------------------------------------
# 4. 메인 화면 - 연동 상태 대시보드 배너 & 챗봇 인터페이스
# ------------------------------------------------------------------------------
st.title("🤖 OpenAI AI 챗봇")

# [핵심] 메인 화면 최상단 연동 상태 안내 알림창
if st.session_state.api_status["valid"]:
    st.success("✅ **시스템 안내:** OpenAI API가 정상적으로 연동되었습니다. 대화를 시작할 수 있습니다.")
else:
    st.warning("⚠️ **시스템 안내:** 왼쪽 사이드바에 유효한 OpenAI API 키를 입력해 주셔야 챗봇이 작동합니다.")

st.divider()

# 대화 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 프롬프트 입력 및 대화 처리
if prompt := st.chat_input("질문을 입력하세요..."):
    # 1차 예외 처리: API 키가 연동되지 않은 경우
    if not st.session_state.api_status["valid"]:
        st.error("❌ API 키가 연동되지 않아 답변을 생성할 수 없습니다. 사이드바에서 키를 등록해 주세요.")
    else:
        # 사용자 메시지 저장 및 표시
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI 답변 생성 및 예외 처리
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ]
                )
                full_response = response.choices[0].message.content
                message_placeholder.markdown(full_response)
                
                # 어시스턴트 답변 저장
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                message_placeholder.error(f"⚠️ 답변 생성 중 오류가 발생했습니다: {str(e)}")