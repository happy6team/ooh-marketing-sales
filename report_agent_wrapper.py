#!/usr/bin/env python
# report_agent_wrapper.py - report_agent.py를 안전하게 실행하는 래퍼

import sys
import os
import subprocess
import json
import traceback
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
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

# --- 파일 존재 확인 ---
if not os.path.exists("report_agent.py"):
    print(json.dumps({
        "success": False,
        "error": "report_agent.py 파일이 존재하지 않습니다."
    }))
    sys.exit(1)

try:
    # --- report_agent.py 직접 실행 (이제는 CLI 인자 사용)
    cmd = [sys.executable, "report_agent.py", f"--brand={brand_name}"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # 디버깅용 로그
    print("=== STDOUT ===")
    print(result.stdout)
    print("=== STDERR ===")
    print(result.stderr)

    # 결과 JSON 파싱 시도
    json_result = None
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                json_result = json.loads(line)
                break
            except:
                continue

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
