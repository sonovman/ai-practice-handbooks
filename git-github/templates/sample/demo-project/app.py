# 핸드북 22 시범용 — 일부러 '올리면 안 되는 값'을 섞어 둔 가짜 프로젝트입니다. 실제 키 아님.
import os

# 나쁜 예: 코드에 키를 직접 박음(하드코딩)
OPENAI_API_KEY = "sk-proj-FAKEdemo1234567890ABCDEFghijklmnop"   # 가짜
DB_URL = "postgresql://admin:SuperSecret123@db.example.com:5432/app"  # 가짜

# 좋은 예: 환경 변수로 읽기
good_key = os.environ.get("OPENAI_API_KEY")
