#!/usr/bin/env python
# report_agent_wrapper.py - report_agent.py 실행을 위한 안전한 래퍼

import sys
import os
import tempfile
import shutil
import json
import time
import traceback
import subprocess
from dotenv import load_dotenv

# --- 명령행 인수 파싱 ---
brand_name = None
brand_issue = None

for arg in sys.argv:
    if arg.startswith('--brand='):
        brand_name = arg.split('=')[1]
    elif arg.startswith('--issue='):
        brand_issue = arg.split('=')[1]

if not brand_name:
    print(json.dumps({
        "success": False,
        "error": "브랜드명이 지정되지 않았습니다."
    }))
    sys.exit(1)

# --- 환경변수 설정 ---
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
os.environ['OPENAI_API_KEY'] = openai_api_key

# --- report_agent.py 경로 확인 ---
if not os.path.exists('report_agent.py'):
    print(json.dumps({
        "success": False,
        "error": "report_agent.py 파일을 찾을 수 없습니다."
    }))
    sys.exit(1)

try:
    # --- 원본 코드 읽기 ---
    with open('report_agent.py', 'r', encoding='utf-8') as f:
        original_code = f.read()

    # --- 코드 수정 ---
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, 'temp_report_agent.py')

    # 브랜드 이름만 바꿔서 state 설정
    modified_code = original_code.replace(
        'initial_state = {\n    "brand_name": "유니클로코리아",\n}',
        f'initial_state = {{\n    "brand_name": "{brand_name}",\n}}'
    )

    # JSON 출력 추가
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
    modified_code = modified_code.replace(
        'print(f"📄 제안서 Word 파일 경로: {final_state[\'proposal_file_path\']}")',
        'print(f"📄 제안서 Word 파일 경로: {final_state[\'proposal_file_path\']}")' + output_json_code
    )

    with open(temp_file_path, 'w', encoding='utf-8') as f:
        f.write(modified_code)

    # --- 수정된 임시 스크립트 실행 ---
    result = subprocess.run(
        [sys.executable, temp_file_path],
        capture_output=True,
        text=True
    )

    # 로그 출력 (디버깅용)
    print("=== STDOUT ===")
    print(result.stdout)
    print("=== STDERR ===")
    print(result.stderr)

    # JSON 결과 추출 시도
    json_result = None
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                json_result = json.loads(line)
                break
            except:
                continue

    shutil.rmtree(temp_dir)  # 임시 디렉토리 제거

    if json_result and json_result.get("success"):
        print(json.dumps(json_result))
        sys.exit(0)
    else:
        print(json.dumps({
            "success": False,
            "error": "JSON 결과를 찾지 못했습니다.",
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
