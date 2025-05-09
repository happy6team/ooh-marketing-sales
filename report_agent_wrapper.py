#!/usr/bin/env python
# report_agent_wrapper.py - report_agent.py를 안전하게 실행하는 래퍼

import sys
import os
import subprocess
import json
import traceback
from dotenv import load_dotenv

def run_report_agent(brand_name: str):
    try:
        # --- 환경변수 로딩 ---
        load_dotenv()
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

        # --- 파일 존재 확인 ---
        if not os.path.exists("report_agent.py"):
            return {
                "success": False,
                "error": "report_agent.py 파일이 존재하지 않습니다."
            }

        # --- report_agent.py 실행 ---
        cmd = [sys.executable, "report_agent.py", f"--brand={brand_name}"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # --- 결과 stdout에서 JSON 파싱 ---
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue

        # --- 실패 시 에러 리턴 ---
        return {
            "success": False,
            "error": "JSON 결과를 찾지 못했습니다.",
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Streamlit 또는 외부에서 호출 가능하도록 함수화
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--brand", required=True)
    args = parser.parse_args()

    result = run_report_agent(args.brand)
    print(json.dumps(result, ensure_ascii=False, indent=2))
