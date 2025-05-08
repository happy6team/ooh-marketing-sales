import streamlit as st
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="영업 자동화 대시보드", layout="wide")

# 세션 상태 초기화 - 처음 로드할 때만 실행
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.company_data = None
    st.session_state.selected_company = None
    st.session_state.selected_company_idx = None
    st.session_state.show_call_modal = False
    st.session_state.call_completed = {}  # 각 회사별 통화 완료 상태를 저장
    st.session_state.proposal_generated = {}  # 각 회사별 제안서 생성 상태를 저장
    st.session_state.email_script_generated = {}  # 각 회사별 이메일 스크립트 생성 상태를 저장
    st.session_state.email_sent = {}  # 각 회사별 이메일 발송 상태를 저장 (추가)
    st.session_state.show_email_modal = False
    st.session_state.expanded_company = None  # 현재 확장된 회사 인덱스

# 메인 타이틀
st.title("영업 자동화 대시보드")

# 사이드바 설정
st.sidebar.title("영업 자동화 필터")

# 담당자 선택
담당자_options = ["손지영", "진실", "이효정"]
selected_담당자 = st.sidebar.selectbox("담당자 선택", 담당자_options, index=0)

# 카테고리 선택
카테고리_options = [
    "패션", "뷰티", "식음료", "전자제품", 
    "인테리어", "건강", "레저", "이커머스", "금융"
]
selected_카테고리 = st.sidebar.selectbox("카테고리 선택", 카테고리_options, index=0)

# 날짜 선택
date_range = st.sidebar.date_input(
    "날짜 범위", 
    value=(datetime.now().date(), datetime.now().date())
)

# 더미 데이터 생성 함수
def get_sample_data():
    return {
        'brands': [
            {
                'name': '삼성전자',
                'issue': '신제품 출시 및 마케팅 강화',
                'description': '글로벌 전자제품 제조업체',
                'manager_email': 'samsung_manager@samsung.com',
                'manager_phone': '02-1234-5678'
            },
            {
                'name': '현대자동차',
                'issue': '전기차 라인업 확대',
                'description': '자동차 제조 및 판매 기업',
                'manager_email': 'hyundai_manager@hyundai.com',
                'manager_phone': '02-2345-6789'
            },
            {
                'name': 'LG생활건강',
                'issue': '해외 시장 진출 확대',
                'description': '화장품 및 생활용품 제조업체',
                'manager_email': 'lg_manager@lgcare.com',
                'manager_phone': '02-3456-7890'
            }
        ]
    }

# 사이드바에 기업 리스트 업데이트 버튼 추가
if st.sidebar.button("기업 리스트 업데이트", use_container_width=True):
    st.session_state.company_data = get_sample_data()
    st.sidebar.success("기업 정보가 업데이트되었습니다!")
    # 초기화
    st.session_state.call_completed = {}
    st.session_state.proposal_generated = {}
    st.session_state.email_script_generated = {}
    st.session_state.email_sent = {}  # 이메일 발송 상태 초기화 (추가)

# 제안서 생성 함수
def generate_proposal(idx):
    if idx is not None:
        # 실제로는 report_agent.py와 email_agent.py를 호출
        st.session_state.proposal_generated[idx] = True
        st.session_state.email_script_generated[idx] = True
        return True
    return False

# 전화 모달 표시
def show_call_modal():
    if st.session_state.show_call_modal and st.session_state.selected_company:
        idx = st.session_state.selected_company_idx
        brand = st.session_state.selected_company
        
        # 알림창 생성
        with st.container():
            st.info(f"📞 **{brand['name']} 전화 스크립트**", icon="📞")
            
            # 스크립트 내용
            st.markdown(f"""
            ### {brand['name']} 담당자와의 통화
            
            **인사말**: 안녕하세요, {selected_담당자}입니다. {brand['name']} 마케팅 담당자님과 통화할 수 있을까요?
            
            **소개**: 저희는 귀사의 {brand['issue']}와 관련하여 마케팅 제안을 드리고 싶습니다.
            
            **주요 내용**:
            1. 귀사의 {brand['issue']} 관련 마케팅 전략 제안
            2. 성공 사례 공유
            3. 구체적인 협업 방안 논의
            
            **마무리**: 더 자세한 내용은 제안서를 통해 전달드리겠습니다. 이메일 주소 확인 부탁드립니다.
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("통화 완료"):
                    st.session_state.show_call_modal = False
                    st.session_state.call_completed[idx] = True
                    st.rerun()
            with col2:
                if st.button("취소", key="cancel_call"):
                    st.session_state.show_call_modal = False
                    st.rerun()

# 이메일 모달 표시
def show_email_modal():
    if st.session_state.show_email_modal and st.session_state.selected_company:
        idx = st.session_state.selected_company_idx  # 인덱스 저장 (추가)
        brand = st.session_state.selected_company
        
        with st.container():
            st.info(f"📧 **{brand['name']} 이메일 발송**", icon="📧")
            
            # 제안서 파일명 (예시)
            proposal_filename = f"{brand['name']}_제안서.pdf"
            
            # 이메일 스크립트 (예시)
            email_script = f"""
            제목: {brand['name']} {brand['issue']} 관련 마케팅 제안
            
            {brand['name']} 담당자님께,
            
            안녕하세요, {selected_담당자}입니다.
            오늘 통화에서 말씀드린 대로 {brand['issue']}와 관련한 마케팅 제안서를 보내드립니다.
            
            첨부된 제안서를 검토하시고 추가 질문이나 의견이 있으시면 언제든지 연락주시기 바랍니다.
            
            감사합니다.
            
            {selected_담당자} 드림
            """
            
            st.text_area("이메일 내용", email_script, height=200)
            
            st.write(f"첨부 파일: {proposal_filename}")
            
            recipient_email = st.text_input("수신자 이메일", value=brand['manager_email'])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("이메일 발송", key="send_email"):
                    st.success(f"{recipient_email}로 이메일이 성공적으로 발송되었습니다.")
                    st.session_state.show_email_modal = False
                    # 이메일 발송 상태 저장 (수정)
                    st.session_state.email_sent[idx] = True
                    st.rerun()
            with col2:
                if st.button("취소", key="cancel_email"):
                    st.session_state.show_email_modal = False
                    st.rerun()

# 모달을 기업 리스트 위에 표시 (중요 UI 변경)
if st.session_state.show_call_modal:
    show_call_modal()
    st.markdown("---")

if st.session_state.show_email_modal:
    show_email_modal()
    st.markdown("---")

# 메인 컨텐츠 영역
if st.session_state.company_data:
    st.subheader("기업 리스트")
    
    # 각 회사 정보와 버튼 표시
    for i, brand in enumerate(st.session_state.company_data['brands']):
        with st.container():
            col1, col2, col3 = st.columns([2, 4, 1])
            
            with col1:
                st.write(f"**{brand['name']}**")
            
            with col2:
                st.write(brand['issue'])
            
            with col3:
                if st.button("추가 정보", key=f"info_{i}"):
                    # 이미 확장된 회사라면 접기, 아니면 확장하기
                    if st.session_state.expanded_company == i:
                        st.session_state.expanded_company = None
                    else:
                        st.session_state.expanded_company = i
                    st.rerun()
            
            # 확장된 회사 정보 표시
            if st.session_state.expanded_company == i:
                st.info(f"""
                **브랜드 설명:** {brand['description']}  
                **담당자 이메일:** {brand['manager_email']}  
                **담당자 전화번호:** {brand['manager_phone']}
                """)
                
                # 버튼들을 오른쪽 하단에 한 줄로 배치
                _, _, button_col = st.columns([2, 2, 3])
                with button_col:
                    # 버튼들을 한 줄에 배치
                    b1, b2, b3, b4 = st.columns(4)
                    
                    # 전화 걸기 버튼
                    with b1:
                        if st.button(f"전화 걸기", key=f"call_{i}"):
                            st.session_state.selected_company = brand
                            st.session_state.selected_company_idx = i
                            st.session_state.show_call_modal = True
                            st.rerun()
                    
                    # 제안서 생성 버튼 - 통화 완료 후에만 활성화
                    with b2:
                        call_completed = i in st.session_state.call_completed and st.session_state.call_completed[i]
                        proposal_generated = i in st.session_state.proposal_generated and st.session_state.proposal_generated[i]
                        
                        if not call_completed:
                            st.button(f"제안서", disabled=True, key=f"proposal_disabled_{i}")
                        else:
                            if st.button(f"제안서", key=f"proposal_{i}"):
                                generate_proposal(i)
                                st.rerun()
                    
                    # 이메일 발송 버튼 - 제안서 생성 후에만 활성화
                    with b3:
                        call_completed = i in st.session_state.call_completed and st.session_state.call_completed[i]
                        proposal_generated = i in st.session_state.proposal_generated and st.session_state.proposal_generated[i]
                        
                        if not call_completed or not proposal_generated:
                            st.button(f"이메일", disabled=True, key=f"email_disabled_{i}")
                        else:
                            if st.button(f"이메일", key=f"email_{i}"):
                                st.session_state.selected_company = brand
                                st.session_state.selected_company_idx = i
                                st.session_state.show_email_modal = True
                                st.rerun()
                    
                    # 접기 버튼
                    with b4:
                        if st.button("접기", key=f"hide_{i}"):
                            st.session_state.expanded_company = None
                            st.rerun()
                
            st.markdown("---")

# 상태 표시
st.sidebar.markdown("---")
st.sidebar.subheader("진행 상태")
if st.session_state.company_data:
    st.sidebar.success("✅ 기업 정보 업데이트 완료")
    
    # 각 회사별 진행 상태 표시
    for i, brand in enumerate(st.session_state.company_data['brands']):
        if i in st.session_state.call_completed and st.session_state.call_completed[i]:
            st.sidebar.success(f"✅ {brand['name']} 통화 완료")
        if i in st.session_state.proposal_generated and st.session_state.proposal_generated[i]:
            st.sidebar.success(f"✅ {brand['name']} 제안서 생성 완료")
        if i in st.session_state.email_script_generated and st.session_state.email_script_generated[i]:
            st.sidebar.success(f"✅ {brand['name']} 이메일 스크립트 생성 완료")
        # 이메일 발송 상태 추가
        if i in st.session_state.email_sent and st.session_state.email_sent[i]:
            st.sidebar.success(f"✅ {brand['name']} 이메일 발송 완료")