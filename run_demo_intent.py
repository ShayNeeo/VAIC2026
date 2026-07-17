import asyncio
import json
import os
from pprint import pprint

# Load .env file manually
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val

from app.intent.extractor import IntentExtractor

async def main():
    print("Khởi tạo Intent Extractor...")
    try:
        extractor = IntentExtractor()
    except Exception as e:
        print(f"Lỗi khởi tạo: {e}")
        return

    # Câu lệnh mẫu (từ SHB B2B context)
    message = "Doanh nghiệp ABC muốn đăng ký chi lương trực tuyến cho 500 nhân sự qua SHB Corporate Online, và xin cấp thêm vốn lưu động tín chấp. Kế toán bảo đang cần gấp thủ tục."
    
    print(f"\nMessage: '{message}'")
    print("Đang gọi LLM (OpenAI) để trích xuất Intent...")
    
    try:
        intent_result = await extractor.extract_intent(message=message, message_id="msg_001")
        
        print("\n=== KẾT QUẢ TRÍCH XUẤT (INTENT RESULT) ===")
        # Dump to dictionary and print as formatted JSON
        result_json = intent_result.model_dump_json(indent=2)
        print(result_json)
        
    except Exception as e:
        print(f"\nLỗi trích xuất: {e}")

if __name__ == "__main__":
    asyncio.run(main())
