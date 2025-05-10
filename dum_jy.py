import json
import os
import subprocess
import sys
import streamlit as st
import pandas as pd
from datetime import datetime

from run_company_media_agent import run_company_media_agent
from call_summary_agent_jy import call_summary_agent

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
    st.session_state.call_summary = {} 
    st.session_state.proposal_files = {}  

# 영업 단계 목록 (단순화)
SALES_STATUS = ["미접촉", "접촉 완료", "제안서 발송", "협의 중", "진행 완료", "영업 실패", "보류"]

# 영업 단계 변경 콜백 함수
def update_sales_status(idx):
    """선택한 영업 단계로 상태 변경"""
    status_key = f"status_select_{idx}"
    if status_key in st.session_state:
        new_status = st.session_state[status_key]
        if st.session_state.company_data is not None and idx < len(st.session_state.company_data):
            st.session_state.company_data.loc[idx, 'sales_status'] = new_status

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

# 사이드바에 업데이트 버튼 추가
if st.sidebar.button("🏢 브랜드 리스트 업데이트", use_container_width=True):
    # 실제 에이전트 실행을 통해 데이터 생성
    with st.spinner("브랜드 리스트업 중... 잠시만 기다려주세요 🙏"):
        # df = run_company_media_agent(selected_카테고리, date_range, selected_담당자)
        
        # 테스트를 위해 파일에서 데이터 로드
        df = pd.read_csv("output_match2.csv")
        
        # 기존 데이터에 담당자 정보 컬럼이 없다면 추가
        if "manager_name" not in df.columns:
            df["manager_name"] = None
        if "manager_email" not in df.columns:
            df["manager_email"] = None
        if "manager_phone_number" not in df.columns:
            df["manager_phone_number"] = None
        
        # 영업 상태 기본값 설정
        if "sales_status" not in df.columns:
            df["sales_status"] = "미접촉"
        
        st.session_state.company_data = df.copy()
        st.sidebar.success("브랜드 리스트가 성공적으로 업데이트되었습니다!")

# 제안서 생성 함수 - report_agent 연동
def generate_proposal(idx):
    if idx is None or st.session_state.company_data is None or st.session_state.company_data.empty:
        st.error("⚠️ 회사 정보가 없습니다.")
        return False, "회사 정보 없음"

    brand = st.session_state.company_data.loc[idx, 'brand_list']
    issue = st.session_state.company_data.loc[idx, 'recent_brand_issues']

    st.warning(f"📣 제안서 생성 시작: {brand}")
    # st.session_state.proposal_generated[idx] = True
    # st.session_state.email_script_generated[idx] = True

    try:
        with st.spinner(f"{brand} 제안서 생성 중..."):
            cmd = [
                sys.executable,
                "report_agent_wrapper.py",
                f"--brand={brand}",
                f"--issue={issue}"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=900
            )

            with st.expander("제안서 생성 로그", expanded=False):
                st.subheader("표준 출력:")
                st.code(result.stdout)
                if result.stderr:
                    st.subheader("오류 출력:")
                    st.code(result.stderr)

            if result.returncode == 0:
                json_result = None
                for line in result.stdout.split('\n'):
                    if line.strip().startswith('{') and line.strip().endswith('}'):
                        try:
                            json_result = json.loads(line.strip())
                            break
                        except json.JSONDecodeError:
                            continue

                if json_result and json_result.get("success"):
                    st.session_state.proposal_generated[idx] = True
                    st.session_state.email_script_generated[idx] = True

                    file_path = json_result.get("file_path", "")
                    if file_path and os.path.exists(file_path):
                        st.success(f"✅ 제안서가 생성되었습니다: {file_path}")
                        with open(file_path, "rb") as file:
                            st.download_button(
                                label="📄 제안서 다운로드",
                                data=file,
                                file_name=os.path.basename(file_path),
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                    st.rerun()
                    return True, "성공"
                else:
                    st.error("❌ JSON 결과가 없거나 실패했습니다.")
                    return False, "JSON 결과 없음"
            else:
                st.error(f"❌ wrapper 실행 실패: 종료 코드 {result.returncode}")
                print("실행코드 종료", result.returncode)
                return False, f"실패: 종료 코드 {result.returncode}"
    except subprocess.TimeoutExpired:
        st.error("⏰ 제안서 생성 시간이 초과되었습니다.")
        return False, "시간 초과"

    except Exception as e:
        st.error(f"❌ 예외 발생: {e}")
        return False, str(e)


# 전화 걸기 다이얼로그 함수
@st.dialog("전화 스크립트")
def show_call_dialog(idx):
    """
    전화 스크립트 다이얼로그를 표시합니다.
    """
    brand_name = working_df.loc[idx, 'brand_list']
    call_script = working_df.loc[idx, 'sales_call_script']
    
    st.markdown(f"### {brand_name} 담당자와의 통화 스크립트")
    st.markdown(f"{call_script}")
    
    # 버튼 컬럼 2개로 수정
    col1, col2 = st.columns(2)
    with col1:
        # 다이얼로그 내의 버튼에 고유한 키 할당
        if st.button("취소", key=f"dialog_cancel_{idx}", use_container_width=True):
            st.rerun()
    with col2:
        # 다이얼로그 내의 버튼에 고유한 키 할당
        if st.button("통화 완료", key=f"dialog_complete_{idx}", type="primary", use_container_width=True):
            # 통화 완료 상태 표시 및 영업 단계 업데이트
            st.session_state.call_completed[idx] = True
            st.session_state.company_data.loc[idx, 'sales_status'] = "접촉 완료"
            
            # 바로 통화 요약 처리 시작 (비동기 방식으로 변경)
            with st.spinner("통화 내용을 분석 중입니다..."):
                call_data = process_call_summary(idx)
                if call_data:
                    st.success(f"{brand_name} 통화 내용이 성공적으로 분석되었습니다.")
            
            st.rerun()

# 통화 요약 다이얼로그 함수 (신규 추가)
@st.dialog("통화 요약")
def show_call_summary_dialog(idx):
    """
    통화 요약 정보를 표시하는 다이얼로그
    """
    brand_name = working_df.loc[idx, 'brand_list']
    
    if idx in st.session_state.call_summary:
        call_data = st.session_state.call_summary[idx]
        
        st.markdown(f"### {brand_name} 담당자와의 통화 요약")
        
        # 통화 요약 정보 표시
        st.markdown("#### 주요 정보")
        st.info(f"""
            **통화 요약:** {call_data.get('call_summary', '정보 없음')}  
            **고객 요구사항:** {call_data.get('client_needs_summary', '정보 없음')}  
            **영업 상태:** {call_data.get('sales_status', '정보 없음')}  
            **비고:** {call_data.get('remarks', '정보 없음')}  
            **연락 시간:** {call_data.get('contact_time', '정보 없음')}  
        """)
        
        # 전체 통화 내용 표시 (확장 가능한 expander 사용)
        with st.expander("전체 통화 내용 보기"):
            st.write(call_data.get('call_full_text', '통화 내용이 없습니다.'))
        
        # 확인 버튼
        if st.button("확인", key=f"summary_ok_{idx}", use_container_width=True):
            st.rerun()
    else:
        st.error("통화 요약 정보가 없습니다. 먼저 통화 분석을 진행해주세요.")
        if st.button("닫기", key=f"summary_close_{idx}", use_container_width=True):
            st.rerun()

# 통화 요약 처리 함수 
def process_call_summary(idx):
    """
    통화 내용을 처리하고 요약하는 함수
    """
    if idx is not None and st.session_state.company_data is not None:
        brand_name = st.session_state.company_data.loc[idx, 'brand_list']
        
        # 담당자 정보 가져오기
        manager_name = st.session_state.company_data.loc[idx, 'manager_name']
        if pd.isna(manager_name) or not manager_name:
            manager_name = "담당자"  # 기본값
        
        manager_email = st.session_state.company_data.loc[idx, 'manager_email']
        if pd.isna(manager_email):
            manager_email = None
        
        # call_summary_agent 호출하여 통화 내용 분석
        call_data = call_summary_agent(brand_name, manager_name, manager_email)
        
        # 세션 상태에 저장
        st.session_state.call_summary[idx] = call_data
        
        # 영업 상태 업데이트
        if 'sales_status' in call_data and call_data['sales_status']:
            st.session_state.company_data.loc[idx, 'sales_status'] = "접촉 완료"
        
        return call_data
    return None


# 이메일 다이얼로그 함수
@st.dialog("이메일 스크립트")
def show_email_dialog(idx):
    """
    이메일 스크립트 다이얼로그를 표시합니다.
    """
    brand_name = working_df.loc[idx, 'brand_list']
    manager_email = working_df.loc[idx, 'manager_email'] if not pd.isna(working_df.loc[idx, 'manager_email']) else ""
    
    # 제안서 파일 경로 확인
    proposal_filename = f"{brand_name}_제안서.pdf"
    if 'proposal_files' in st.session_state and idx in st.session_state.proposal_files:
        proposal_filepath = st.session_state.proposal_files[idx]
        proposal_filename = os.path.basename(proposal_filepath)
    
    st.markdown(f"### {brand_name} 담당자에게 이메일 발송")
    
    # 첨부 파일 정보 표시
    st.text(f"첨부 파일: {proposal_filename}")
    
    # 수신자 이메일 입력
    recipient_email = st.text_input("수신자 이메일", value=manager_email, key=f"recipient_email_{idx}")
    
    # 이메일 내용
    default_email = f"""안녕하세요.  
옥외광고 매체사 <올이즈굿>의 광고팀 {selected_담당자} 매니저입니다.

{brand_name}에 적합한 옥외광고인  
{working_df.loc[idx, 'matched_media']}를 소개해 드리고자 메일을 남기게 되었습니다.

{working_df.loc[idx, 'matched_media']}은 월평균 약 185만명의 여객 수를 기록하고 있어, 다양한 연령대(20-60대)의 고객층에게 도달할 수 있는 기회를 제공합니다.

첨부된 소개서에서 관련 매체들을 확인하실 수 있습니다.  
확인 후 회신 주시면, 전화나 미팅을 통해 더 자세히 안내해 드리겠습니다 :)

긴 메일 읽어주셔서 감사합니다.  
올이즈굿 {selected_담당자} 드림
"""
    
    email_script = working_df.loc[idx, 'proposal_email'] if 'proposal_email' in working_df.columns and not pd.isna(working_df.loc[idx, 'proposal_email']) else default_email
    
    st.text_area("이메일 내용", email_script, height=300, key=f"email_content_{idx}")
    
    col1, col2 = st.columns(2)
    with col1:
        # 취소 버튼
        if st.button("취소", key=f"email_dialog_cancel_{idx}", use_container_width=True):
            st.rerun()
    with col2:
        # 이메일 발송 버튼
        if st.button("이메일 발송", key=f"email_dialog_send_{idx}", type="primary", use_container_width=True):
            # 이메일 발송 처리
            if 'proposal_files' in st.session_state and idx in st.session_state.proposal_files:
                file_path = st.session_state.proposal_files[idx]
                # 여기서 실제 이메일 발송 코드가 들어갈 수 있습니다
                st.session_state.email_sent[idx] = True
                st.success(f"{recipient_email}로 이메일이 성공적으로 발송되었습니다.")
            else:
                st.session_state.email_sent[idx] = True
                st.warning(f"{recipient_email}로 이메일이 발송되었습니다. (제안서 파일 첨부 없음)")
            
            # 영업 단계 업데이트
            st.session_state.company_data.loc[idx, 'sales_status'] = "제안서 발송"
            st.rerun()



# 작업할 데이터 설정 및 표시
if st.session_state.company_data is not None:
        working_df = st.session_state.company_data
        
        # 브랜드 리스트
        st.subheader("브랜드 리스트")
        
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 6, 2, 1])
            with col1:
                st.write("브랜드 명")
            with col2:
                st.write("최신 이슈")
            with col3:
                st.write("영업 단계")
            with col4:
                st.write("추가 정보")
        
        st.markdown("---")
        
        for i in range(st.session_state.company_data.shape[0]):
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 6, 2, 1])
        
                with col1:
                    st.write(f"**{working_df.loc[i, 'brand_list']}**")
                with col2:
                    st.write(f"{working_df.loc[i, 'recent_brand_issues']}")
                with col3:
                    # 영업 단계 표시 (단순 텍스트만)
                    st.write(f"{working_df.loc[i, 'sales_status']}")
        
                with col4:
                    # 고유한 키 사용
                    if st.button("확인하기", key=f"info_btn_{i}"):
                        # 이미 확장된 회사라면 접기, 아니면 확장하기
                        if st.session_state.expanded_company == i:
                            st.session_state.expanded_company = None
                        else:
                            st.session_state.expanded_company = i
                        st.rerun()


                # 확장된 회사 정보 표시
                if st.session_state.expanded_company == i:
                    # # 비동기 처리 확인 및 처리 (스피너 없음)
                    # processing_key = f"processing_call_{i}"
                    # if processing_key in st.session_state and st.session_state[processing_key]:
                    #     # 스피너 없이 통화 요약 처리 함수 호출 (함수 내부에 스피너 있음)
                    #     process_call_summary(i)
                    #     # 처리 완료 후 플래그 제거
                    #     st.session_state.pop(processing_key, None)
                    #     st.rerun()
                    
                    st.info(f"""
                        **카테고리:** {working_df.loc[i, "category"]}  
                        **브랜드 설명:** {working_df.loc[i, "core_product_summary"]}  
                        **추천 매체:** {working_df.loc[i, "matched_media"]}  
                        **추천 이유:** {working_df.loc[i, "match_reason"]}  
                    """)


                    with st.container():
                        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
                        # 현재 값 가져오기 (None이면 빈 문자열로 처리)
                        current_name = "" if pd.isna(working_df.loc[i, "manager_name"]) else working_df.loc[i, "manager_name"]
                        current_email = "" if pd.isna(working_df.loc[i, "manager_email"]) else working_df.loc[i, "manager_email"]
                        current_phone = "" if pd.isna(working_df.loc[i, "manager_phone_number"]) else working_df.loc[i, "manager_phone_number"]
        
                        with col1:
                            manager_name = st.text_input("브랜드 담당자 이름", value=current_name, key=f"name_input_{i}")
                            if manager_name:  # 값이 있는 경우에만 저장
                                st.session_state.company_data.loc[i, "manager_name"] = manager_name
                        
                        with col2: 
                            manager_email = st.text_input("브랜드 담당자 이메일", value=current_email, key=f"email_input_{i}")
                            if manager_email:
                                st.session_state.company_data.loc[i, "manager_email"] = manager_email
                        
                        with col3:
                            manager_phone = st.text_input("브랜드 담당자 전화번호", value=current_phone, key=f"phone_input_{i}")
                            if manager_phone:
                                st.session_state.company_data.loc[i, "manager_phone_number"] = manager_phone
    
                        with col4:
                            # 영업 단계 선택 (콜백 사용)
                            # 현재 영업 단계 표시
                            current_status = working_df.loc[i, 'sales_status']
                            
                            # 영업 단계 선택 - 상태가 변경되면 콜백 함수로 바로 적용
                            new_status = st.selectbox(
                                "선택하면 자동으로 저장됩니다",
                                options=SALES_STATUS,
                                index=SALES_STATUS.index(current_status) if current_status in SALES_STATUS else 0,
                                key=f"status_select_{i}",
                                on_change=update_sales_status,
                                args=(i,)
                            )
                            
                    
                    # 버튼들을 오른쪽 하단에 한 줄로 배치
                    _, _, button_col = st.columns([1, 1, 2])
                    
                    with button_col:
                        # 버튼들을 한 줄에 배치
                        b1, b2, b3, b4, b5 = st.columns(5) 
                        
                        # 전화 걸기 버튼 - 고유한 키 사용
                        with b1:
                            call_completed = i in st.session_state.call_completed and st.session_state.call_completed[i]
                            call_button_label = "✓ 통화 완료" if call_completed else "전화 걸기"
                            
                            # 키 값을 명확하게 구분
                            if st.button(call_button_label, key=f"call_btn_{i}"):
                                if not call_completed:
                                    show_call_dialog(i)


                        with b2:
                            call_completed = i in st.session_state.call_completed and st.session_state.call_completed[i]
                            has_summary = i in st.session_state.call_summary
                            
                            if call_completed:
                                # 여기를 수정: summary_button_type 제거하고 체크 표시 추가
                                summary_button_label = "✓ 통화 요약" if has_summary else "통화 요약"
                                if st.button(summary_button_label, key=f"summary_btn_{i}"):
                                    show_call_summary_dialog(i)
                            else:
                                st.button("통화 요약", key=f"summary_disabled_{i}", disabled=True)
                        
                        # 제안서 생성 버튼 - 통화 완료 후에만 활성화
                        with b3:
                            call_completed = i in st.session_state.call_completed and st.session_state.call_completed[i]
                            proposal_generated = i in st.session_state.proposal_generated and st.session_state.proposal_generated[i]
                            
                            proposal_button_label = "✓ 제안서 완료" if proposal_generated else "제안서 생성"
                            
                            if not call_completed:
                                st.button(proposal_button_label, disabled=True, key=f"proposal_disabled_{i}")
                            else:
                                if st.button(proposal_button_label, key=f"proposal_{i}"):
                                    generate_proposal(i)
                                    st.rerun()
                        
                        # 이메일 발송 버튼 - 제안서 생성 후에만 활성화
                        with b4:
                            call_completed = i in st.session_state.call_completed and st.session_state.call_completed[i]
                            proposal_generated = i in st.session_state.proposal_generated and st.session_state.proposal_generated[i]
                            email_sent = i in st.session_state.email_sent and st.session_state.email_sent[i]
                            
                            email_button_label = "✓ 이메일 완료" if email_sent else "이메일 발송"
                            
                            if not call_completed or not proposal_generated:
                                st.button(email_button_label, disabled=True, key=f"email_disabled_{i}")
                            else:
                                if st.button(email_button_label, key=f"email_{i}"):
                                    show_email_dialog(i)
                        
                        # 접기 버튼 - 고유한 키 사용
                        with b5:
                            if st.button("접기", key=f"hide_btn_{i}"):
                                st.session_state.expanded_company = None
                                st.rerun()
        
                    st.markdown("---")
        
        # 상태 표시
        st.sidebar.markdown("---")
        st.sidebar.subheader("진행 상태")
        
        # 상태 정보를 저장할 리스트
        status_items = []

        # 각 회사별 진행 상태 수집
        for i in range(st.session_state.company_data.shape[0]):
            brand_name = working_df.loc[i, 'brand_list']
            
            if i in st.session_state.email_sent and st.session_state.email_sent[i]:
                status_items.append({"status": "이메일 발송 완료", "brand": brand_name, "priority": 5})
            
            if i in st.session_state.email_script_generated and st.session_state.email_script_generated[i]:
                status_items.append({"status": "이메일 스크립트 생성 완료", "brand": brand_name, "priority": 4})
            
            if i in st.session_state.proposal_generated and st.session_state.proposal_generated[i]:
                status_items.append({"status": "제안서 생성 완료", "brand": brand_name, "priority": 3})
            
            # 통화 요약 추가
            if i in st.session_state.call_summary:
                status_items.append({"status": "통화 요약 완료", "brand": brand_name, "priority": 2})
            
            if i in st.session_state.call_completed and st.session_state.call_completed[i]:
                status_items.append({"status": "통화 완료", "brand": brand_name, "priority": 1})

        # 우선순위 기준으로 내림차순 정렬 (최근 처리된 항목이 위에 표시)
        status_items.sort(key=lambda x: x["priority"], reverse=True)

        # 정렬된 상태 표시
        for item in status_items:
            st.sidebar.success(f"✅ {item['brand']} {item['status']}")
else:
    # 데이터가 없을 때 메시지 표시
    st.info("👈 브랜드 리스트를 보려면 왼쪽 사이드바에서 필터 설정 후 '브랜드 리스트 업데이트' 버튼을 클릭하세요.")