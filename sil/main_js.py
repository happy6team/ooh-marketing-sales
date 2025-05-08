import streamlit as st
import pandas as pd
from datetime import datetime
import subprocess
import os
from dotenv import load_dotenv
load_dotenv()

# 디버깅용 출력
import os
if os.getenv("OPENAI_API_KEY"):
    print("✅ OPENAI_API_KEY 로드됨")
else:
    print("⚠️ OPENAI_API_KEY 없음")

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
    st.session_state.email_sent = {}  # 각 회사별 이메일 발송 상태를 저장
    st.session_state.show_email_modal = False
    st.session_state.expanded_company = None  # 현재 확장된 회사 인덱스
    st.session_state.report_results = {}  # 제안서 생성 결과를 저장

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
                'name': '유니클로 코리아',
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
    st.session_state.email_sent = {}
    st.session_state.report_results = {}

# 제안서 생성 함수 - 실제 report_agent.py 실행

def generate_proposal(idx):
    if idx is not None and st.session_state.company_data:
        brand = st.session_state.company_data['brands'][idx]
        
        try:
            with st.spinner(f"{brand['name']} 제안서 생성 중... (AI 처리로 시간이 걸릴 수 있습니다)"):
                import sys
                import subprocess
                import json
                import os
                import time
                
                # 래퍼 스크립트 생성
                wrapper_script = 'report_agent_wrapper.py'
                if not os.path.exists(wrapper_script):
                    st.info("래퍼 스크립트를 생성합니다...")
                    
                    with open(wrapper_script, 'w', encoding='utf-8') as f:
                        f.write('''#!/usr/bin/env python
# report_agent_wrapper.py - 원본 report_agent.py를 수정하지 않고 실행하는 래퍼
import sys
import os
import tempfile
import shutil
import json
import time
import traceback

# 명령행 인수 처리
brand_name = None
brand_issue = None

for arg in sys.argv:
    if arg.startswith('--brand='):
        brand_name = arg.split('=')[1]
    if arg.startswith('--issue='):
        brand_issue = arg.split('=')[1]

if not brand_name:
    print(json.dumps({
        "success": False,
        "error": "브랜드명이 지정되지 않았습니다."
    }))
    sys.exit(1)

print(f"브랜드명: {brand_name}, 이슈: {brand_issue}")

# 원본 report_agent.py 파일이 있는지 확인
if not os.path.exists('report_agent.py'):
    print(json.dumps({
        "success": False,
        "error": "report_agent.py 파일을 찾을 수 없습니다."
    }))
    sys.exit(1)

# 필요한 환경 변수 설정 (예: OpenAI API 키)
os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', '')

try:
    # 원본 파일 읽기
    with open('report_agent.py', 'r', encoding='utf-8') as f:
        original_code = f.read()
    
    # 임시 수정 파일을 위한 디렉토리 생성
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, 'temp_report_agent.py')
    
    # 코드 수정: initial_state에 브랜드명 교체
    modified_code = original_code.replace(
        'initial_state = {\\n    "brand_name": "유니클로코리아",\\n}',
        f'initial_state = {{\\n    "brand_name": "{brand_name}",\\n}}'
    )
    
    # 코드 수정: 결과를 JSON으로 출력하는 코드 추가
    output_json_code = """
# JSON 결과 출력
import json
result = {
    "success": True,
    "brand": initial_state["brand_name"],
    "file_path": final_state["proposal_file_path"],
    "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
}
print(json.dumps(result))
"""
    
    # 결과 출력 코드 추가
    modified_code = modified_code.replace(
        'print(f"📄 제안서 Word 파일 경로: {final_state[\\\'proposal_file_path\\\']}")',
        'print(f"📄 제안서 Word 파일 경로: {final_state[\\\'proposal_file_path\\\']}")' + output_json_code
    )
    
    # 수정된 코드를 임시 파일에 저장
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        f.write(modified_code)
    
    print(f"임시 파일 생성 완료: {temp_file_path}")
    
    # 임시 파일 실행
    print("임시 파일 실행 중...")
    
    # 원래 os.system 대신 subprocess 사용으로 변경
    import subprocess
    result = subprocess.run([sys.executable, temp_file_path], capture_output=True, text=True)
    
    # 임시 디렉토리 삭제
    shutil.rmtree(temp_dir)
    
    # 출력 결과에서 JSON 형식 찾기
    import re
    json_result = None
    
    for line in result.stdout.split('\\n'):
        if line.strip().startswith('{') and line.strip().endswith('}'):
            try:
                json_result = json.loads(line.strip())
                break
            except:
                pass
                
    if json_result and json_result.get('success'):
        print(json.dumps(json_result))
        sys.exit(0)
    else:
        print(json.dumps({
            "success": False,
            "error": "JSON 결과를 찾을 수 없습니다.",
            "stdout": result.stdout,
            "stderr": result.stderr
        }))
        sys.exit(1)
        
except Exception as e:
    print(json.dumps({
        "success": False,
        "error": str(e),
        "traceback": traceback.format_exc()
    }))
    sys.exit(1)
''')
                    
                    st.success(f"래퍼 스크립트 {wrapper_script} 생성 완료!")
                
                # 원본 report_agent.py 파일 확인
                if not os.path.exists('report_agent.py'):
                    st.error("⚠️ report_agent.py 파일이 존재하지 않습니다!")
                    return False, "report_agent.py 파일이 존재하지 않습니다."
                
                # 환경 변수 설정 및 확인 (디버깅 정보)
                with st.expander("환경 및 파일 정보", expanded=False):
                    st.write(f"현재 작업 디렉토리: {os.getcwd()}")
                    st.write(f"report_agent.py 존재 여부: {os.path.exists('report_agent.py')}")
                    st.write(f"래퍼 스크립트 존재 여부: {os.path.exists(wrapper_script)}")
                    
                    # API 키 확인 (보안 문제로 키 자체는 표시하지 않음)
                    if 'OPENAI_API_KEY' in os.environ:
                        st.success("✅ OPENAI_API_KEY 환경 변수가 설정되어 있습니다.")
                    else:
                        st.warning("⚠️ OPENAI_API_KEY 환경 변수가 설정되어 있지 않습니다.")
                    
                    # .env 파일 확인
                    if os.path.exists('.env'):
                        st.success("✅ .env 파일이 존재합니다.")
                    else:
                        st.warning("⚠️ .env 파일이 존재하지 않습니다.")
                
                # 래퍼 스크립트 실행
                cmd = [
                    sys.executable,
                    wrapper_script,
                    f"--brand={brand['name']}"
                ]
                
                if brand.get('issue'):
                    cmd.append(f"--issue={brand['issue']}")
                
                st.write("래퍼 스크립트를 실행합니다...")
                st.write(f"명령: {' '.join(cmd)}")
                
                try:
                    # 타임아웃을 길게 설정 (AI 모델 처리 시간 고려)
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=900  # 15분
                    )
                    
                    # 실행 로그 표시
                    with st.expander("실행 로그", expanded=False):
                        st.subheader("표준 출력:")
                        st.code(result.stdout)
                        
                        if result.stderr:
                            st.subheader("오류 출력:")
                            st.code(result.stderr)
                    
                    if result.returncode == 0:
                        # JSON 결과 찾기
                        json_result = None
                        for line in result.stdout.split('\n'):
                            if line.strip().startswith('{') and line.strip().endswith('}'):
                                try:
                                    json_result = json.loads(line.strip())
                                    if 'success' in json_result:
                                        break
                                except:
                                    pass
                        
                        if json_result and json_result.get('success', False):
                            # 성공적으로 실행됨
                            st.session_state.proposal_generated[idx] = True
                            st.session_state.report_results[idx] = json.dumps(json_result)
                            
                            # 이메일 스크립트 생성 완료로 표시
                            st.session_state.email_script_generated[idx] = True
                            
                            # 제안서 파일 확인 및 다운로드 버튼
                            file_path = json_result.get('file_path', '')
                            if file_path and os.path.exists(file_path):
                                st.success(f"✅ 제안서 파일이 생성되었습니다: {file_path}")
                                
                                # 다운로드 버튼 추가
                                try:
                                    with open(file_path, "rb") as file:
                                        st.download_button(
                                            label="📄 제안서 다운로드",
                                            data=file,
                                            file_name=os.path.basename(file_path),
                                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                        )
                                except Exception as e:
                                    st.warning(f"파일 다운로드 버튼 생성 중 오류: {e}")
                            
                            return True, "제안서가 성공적으로 생성되었습니다."
                        else:
                            # JSON 결과는 찾았지만 실패 상태
                            if json_result:
                                error_msg = json_result.get('error', '알 수 없는 오류')
                                st.error(f"제안서 생성 실패: {error_msg}")
                                return False, f"제안서 생성 실패: {error_msg}"
                            else:
                                # JSON 결과를 찾지 못함
                                st.error("제안서 생성 과정에서 오류가 발생했습니다.")
                                return False, "제안서 생성 과정에서 오류가 발생했습니다."
                    else:
                        # 실행 자체가 실패
                        st.error(f"래퍼 스크립트 실행 실패: 종료 코드 {result.returncode}")
                        return False, f"래퍼 스크립트 실행 실패: 종료 코드 {result.returncode}"
                
                except subprocess.TimeoutExpired:
                    st.error("제안서 생성 시간이 초과되었습니다 (15분).")
                    return False, "제안서 생성 시간 초과"
                    
                except Exception as e:
                    import traceback
                    st.error(f"래퍼 스크립트 실행 중 오류 발생: {e}")
                    with st.expander("오류 상세"):
                        st.code(traceback.format_exc())
                    return False, f"오류: {e}"
        
        except Exception as e:
            import traceback
            st.error(f"예상치 못한 오류가 발생했습니다: {e}")
            with st.expander("상세 오류"):
                st.code(traceback.format_exc())
            return False, f"오류: {e}"
    
    return False, "기업 정보가 없습니다."

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
        idx = st.session_state.selected_company_idx
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
                    st.session_state.email_sent[idx] = True
                    st.rerun()
            with col2:
                if st.button("취소", key="cancel_email"):
                    st.session_state.show_email_modal = False
                    st.rerun()

# 모달을 기업 리스트 위에 표시
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
        # 이메일 발송 완료 체크
        email_completed = i in st.session_state.email_sent and st.session_state.email_sent[i]
        
        with st.container():
            col1, col2, col3, col4 = st.columns([0.5, 2, 4, 1])
            
            # 체크박스 표시 (이메일 발송 완료 시)
            with col1:
                if email_completed:
                    st.markdown("✅")
                else:
                    st.write("")
            
            with col2:
                st.write(f"**{brand['name']}**")
            
            with col3:
                st.write(brand['issue'])
            
            with col4:
                if st.button("추가 정보", key=f"info_{i}"):
                    # 이미 확장된 회사라면 접기, 아니면 확장하기
                    if st.session_state.expanded_company == i:
                        st.session_state.expanded_company = None
                    else:
                        st.session_state.expanded_company = i
                    st.rerun()
            
            # 확장된 회사 정보 표시
            if st.session_state.expanded_company == i:
                # 추가 정보를 더 잘 구분하기 위해 약간의 들여쓰기 추가
                _, info_col = st.columns([0.5, 9.5])
                with info_col:
                    st.info(f"""
                    **브랜드 설명:** {brand['description']}  
                    **담당자 이메일:** {brand['manager_email']}  
                    **담당자 전화번호:** {brand['manager_phone']}
                    """)
                    
                    # 제안서 생성 결과 표시 (있는 경우)
                    if i in st.session_state.report_results and st.session_state.report_results[i]:
                        try:
                            # JSON 문자열인 경우 파싱 시도
                            import json
                            try:
                                report_data = json.loads(st.session_state.report_results[i])
                                st.success(f"제안서 파일: {report_data.get('file_path', '파일명 없음')}")
                            except:
                                # JSON이 아니면 그냥 텍스트로 표시
                                st.success(f"제안서 생성 결과: {st.session_state.report_results[i]}")
                        except:
                            st.success("제안서가 생성되었습니다.")
                    
                    # 버튼 행 (중첩 열 대신 나란히 배치)
                    button_container = st.container()
                    with button_container:
                        # 버튼을 가로로 정렬하기 위한 CSS 추가
                        st.markdown("""
                        <style>
                        .stButton {
                            display: inline-block;
                            margin-right: 10px;
                        }
                        </style>
                        """, unsafe_allow_html=True)
                        
                        # 전화 걸기 버튼
                        call_completed = i in st.session_state.call_completed and st.session_state.call_completed[i]
                        proposal_generated = i in st.session_state.proposal_generated and st.session_state.proposal_generated[i]
                        
                        # 버튼들을 같은 줄에 배치
                        cols = st.columns([1, 1, 1, 1])
                        
                        # 전화 걸기 버튼
                        with cols[0]:
                            if st.button(f"전화 걸기", key=f"call_{i}"):
                                st.session_state.selected_company = brand
                                st.session_state.selected_company_idx = i
                                st.session_state.show_call_modal = True
                                st.rerun()
                        
                        # 제안서 생성 버튼
                        with cols[1]:
                            if not call_completed:
                                st.button(f"제안서 생성", disabled=True, key=f"proposal_disabled_{i}")
                            else:
                                if st.button(f"제안서 생성", key=f"proposal_{i}"):
                                    success, message = generate_proposal(i)
                                    if success:
                                        st.success(message)
                                    else:
                                        st.error(message)
                                    st.rerun()
                        
                        # 이메일 발송 버튼
                        with cols[2]:
                            if not call_completed or not proposal_generated:
                                st.button(f"이메일 발송", disabled=True, key=f"email_disabled_{i}")
                            else:
                                if st.button(f"이메일 발송", key=f"email_{i}"):
                                    st.session_state.selected_company = brand
                                    st.session_state.selected_company_idx = i
                                    st.session_state.show_email_modal = True
                                    st.rerun()
                        
                        # 접기 버튼
                        with cols[3]:
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
        if i in st.session_state.email_sent and st.session_state.email_sent[i]:
            st.sidebar.success(f"✅ {brand['name']} 이메일 발송 완료")

# 임시 파일 정보 표시 (개발 환경에서만 표시)
if "created_temp_report_agent" in st.session_state and st.session_state["created_temp_report_agent"]:
    st.sidebar.markdown("---")
    st.sidebar.info("참고: 개발 편의를 위해 임시 report_agent.py 파일이 생성되었습니다.")