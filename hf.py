import base64
import io
import os

from groq import Groq
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError
from PIL import Image


# 1. 사용할 수 있는 모델
#    image-to-text 태그 모델(BLIP 등)은 현재 HF Inference API 제공사가 없음
#    -> 이미지를 입력받는 채팅 모델(image-text-to-text)에게 "이미지 설명" 을 요청
HF_MODELS = [
    "google/gemma-4-26B-A4B-it",    # 빠름 (약 3초)
    "Qwen/Qwen3.6-35B-A3B",         # 약 15~20초
    "Qwen/Qwen3.5-9B",              # 약 25~30초
]
GROQ_MODEL = "openai/gpt-oss-120b"

# 2. 프롬프트는 영어로 작성 (한글은 토큰을 더 많이 씀)
SYSTEM_PROMPT = "You are an image captioning assistant. Reply with the description only, in plain English, without markdown."
STYLES = {
    "짧게 (한 문장)": "Describe this image in one sentence.",
    "자세히 (한 문단)": "Describe this image in one paragraph: main subject, background, colors, and mood.",
}
TRANSLATE_PROMPT = "Translate the user's English text into natural Korean. Reply with the translation only."

# 큰 이미지는 이 크기(px)로 줄여서 보냄 -> 전송량 절약
MAX_SIZE = 1024


# 3. 이미지 -> base64 data URL (API 에 이미지를 글자로 바꿔서 보냄)
def to_data_url(image):
    image = image.convert("RGB")            # PNG 투명 배경 등은 JPEG 로 저장할 수 없음
    image.thumbnail((MAX_SIZE, MAX_SIZE))   # 비율 유지하며 줄임 (작은 이미지는 그대로)
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


# 4. HF 모델에게 이미지 설명 요청 -> 영어 설명 글
def describe(image_bytes, model, style):
    client = InferenceClient(api_key=os.getenv("HF_TOKEN"))
    image = Image.open(io.BytesIO(image_bytes))
    response = client.chat.completions.create(
        model=model,
        max_tokens=1024,        # Qwen 은 답하기 전 '생각' 에 토큰을 써서 넉넉하게
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": STYLES[style]},
                {"type": "image_url", "image_url": {"url": to_data_url(image)}},
            ]},
        ],
    )
    text = response.choices[0].message.content
    if not text:
        raise RuntimeError("모델이 빈 답변을 보냈습니다. 다른 모델로 다시 시도하세요.")
    return text.strip()


# 5. Groq 로 한국어 번역 (GROQ_API_KEY 가 없으면 None -> 번역 건너뜀)
def translate_ko(text):
    if not os.getenv("GROQ_API_KEY"):
        return None
    response = Groq().chat.completions.create(     # GROQ_API_KEY 환경변수를 자동으로 읽음
        model=GROQ_MODEL,
        reasoning_effort="low",     # 번역은 low 로 충분 -> 빠르고 토큰 절약
        messages=[
            {"role": "system", "content": TRANSLATE_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content.strip()


# 6. 오류 -> 한글 안내 메시지
def error_message(e):
    if isinstance(e, HfHubHTTPError) and e.response is not None:
        code = e.response.status_code
        if code == 401:
            return "HF_TOKEN 이 올바르지 않거나 만료됐습니다. README 의 '토큰 발급받기' 를 참고해 새로 넣어주세요."
        if code == 402:
            return "이번 달 HF 무료 사용량을 모두 썼습니다. 다음 달에 다시 시도하거나 결제 설정을 확인하세요."
        if code == 429:
            return "요청이 너무 많습니다. 잠시 후 다시 시도하세요."
        return f"Hugging Face API 오류 ({code}) : {e}"
    if isinstance(e, StopIteration):
        return "이 모델을 실행해 주는 HF 제공사가 없습니다. 다른 모델을 고르세요."
    return f"오류가 발생했습니다 : {e}"
