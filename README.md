# 🖼️ 이미지 설명 생성기 (261020_bucheon_huggingface_yjy)

> Hugging Face Inference API로 만든 Image-to-Text 서비스

이미지를 올리면 **Hugging Face 모델이 이미지를 보고 영어 설명(캡션)을 쓰고**, **Groq가 한국어로 번역**하는 **Streamlit 웹 앱**입니다.

> 예) 독수리 사진 → "A bald eagle flies through the air with its large wings spread wide…" → "대머리 독수리가 큰 날개를 활짝 펴고 하늘을 날아다닌다."

---

## 📑 목차

1. [기능](#-기능)
2. [폴더 구조](#-폴더-구조)
3. [사용한 모델](#-사용한-모델)
4. [처음 설치하기 (따라하기)](#-처음-설치하기-따라하기)
5. [토큰 발급받기](#-토큰-발급받기)
6. [.env 파일 만들기](#-env-파일-만들기)
7. [실행하기](#-실행하기)
8. [사용법](#-사용법)
9. [토큰 절약](#-토큰-절약)
10. [문제 해결](#-문제-해결)
11. [처음 요구사항 (구현 프롬프트)](#-처음-요구사항-구현-프롬프트)

---

## ✨ 기능

| 기능 | 설명 |
|---|---|
| 이미지 올리기 | JPG / PNG / WEBP를 끌어다 놓거나 직접 선택 |
| 이미지 설명 | Hugging Face 모델이 이미지를 보고 영어로 설명 |
| 설명 길이 선택 | **짧게(한 문장)** / **자세히(한 문단: 주제·배경·색·분위기)** |
| 모델 선택 | 사이드바에서 HF 모델 3종 중 선택 |
| 한국어 번역 | Groq(`openai/gpt-oss-120b`)가 한국어로 번역. `GROQ_API_KEY`가 없으면 번역만 끔 |
| 사진 회전 보정 | 스마트폰으로 세로로 찍은 사진도 바른 방향으로 모델에 전달 (EXIF 회전 정보 적용) |
| 오류 안내 | 토큰 없음·만료, 사용량 초과, 요청 과다, 인터넷 끊김 등을 한글로 안내. 번역만 실패하면 영어 설명은 그대로 보여줌 |

### 처리 흐름

```
① 이미지 업로드 (app.py)
     │  hf.to_data_url()     회전 보정 → 1024px 이하로 줄이고 JPEG → base64 글자로 변환
     ▼
② Hugging Face Inference API
     │  hf.describe()        영어 프롬프트 + 이미지 → 영어 설명
     ▼
③ Groq API
     │  hf.translate_ko()    영어 설명 → 한국어 번역
     ▼
④ 화면에 영어 / 한국어 결과 표시
```

---

## 📁 폴더 구조

```
261020_bucheon_hugging_yjy/
├── app.py            # Streamlit 화면 (업로드, 설정, 결과 표시)
├── hf.py             # HF 이미지 설명 + Groq 번역 + 오류 메시지
├── requirements.txt  # 필요한 라이브러리 목록
├── .env.example      # .env 예시 (키 값은 비어 있음)
├── .gitignore        # .env 등 비밀 파일을 GitHub에 올리지 않도록 제외
└── README.md
```

---

## 🤖 사용한 모델

### 왜 `image-to-text` 태그 모델이 아닌가요?
[image-to-text 모델 목록](https://huggingface.co/models?pipeline_tag=image-to-text&sort=trending)에 있는 BLIP, ViT-GPT2, Florence-2 등을 먼저 시험했지만,
**2026-10-20 기준으로 이 모델들을 실행해 주는 Inference Provider가 없어서** API 호출이 실패했습니다 (`StopIteration`).

그래서 **이미지를 입력받는 채팅 모델(`image-text-to-text`)** 에 *"Describe this image"* 라고 요청하는 방식으로 같은 기능(이미지 → 텍스트)을 만들었습니다.

| 모델 | 속도 (테스트) | 비고 |
|---|---|---|
| `google/gemma-4-26B-A4B-it` | 약 3초 | **기본값**, 가장 빠름 |
| `Qwen/Qwen3.6-35B-A3B` | 약 18초 | 답하기 전 '생각'하는 시간이 있음 |
| `Qwen/Qwen3.5-9B` | 약 27초 | 〃 |

---

## 🛠 처음 설치하기 (따라하기)

### 1) 레포 받기
```bash
git clone https://github.com/Youkjooyoung/261020_bucheon_huggingface_yjy.git
cd 261020_bucheon_huggingface_yjy
```

### 2) 가상환경 만들기 (conda 예시)
```bash
conda create -n py311 python=3.11 -y
conda activate py311
```

### 3) 라이브러리 설치
```bash
pip install -r requirements.txt
```

| 라이브러리 | 용도 |
|---|---|
| `streamlit` | 웹 화면 |
| `huggingface_hub` | HF Inference API 호출 (`InferenceClient`) |
| `groq` | 한국어 번역 |
| `python-dotenv` | `.env`에서 키 읽기 |
| `pillow` | 이미지 회전 보정·크기 줄이기·JPEG 변환 |
| `httpx` | 인터넷 연결 오류 구분 (huggingface_hub와 함께 설치됨) |

---

## 🔑 토큰 발급받기

### Hugging Face 토큰 (`HF_TOKEN`, 필수)
1. https://huggingface.co 에 로그인
2. 오른쪽 위 프로필 → **Settings → Access Tokens** (https://huggingface.co/settings/tokens)
3. **Create new token** → Token type: **Read** 또는 **Fine-grained**
   - Fine-grained라면 **"Make calls to Inference Providers"** 를 체크
4. 만들어진 `hf_...` 값을 복사

> 무료 계정은 매달 일정량의 무료 사용량(크레딧)이 있습니다.

### Groq API 키 (`GROQ_API_KEY`, 선택 - 번역용)
1. https://console.groq.com/keys 에 로그인
2. **Create API Key** → `gsk_...` 값을 복사

---

## 📝 .env 파일 만들기

`.env.example`을 복사해서 이름을 `.env`로 바꾸고 값을 넣습니다.

```bash
# Windows PowerShell
copy .env.example .env
```

```env
HF_TOKEN=hf_여기에_본인_토큰
GROQ_API_KEY=gsk_여기에_본인_키
```

> ⚠️ `.env`는 `.gitignore`에 들어 있어서 **GitHub에 올라가지 않습니다.** 키를 코드에 직접 쓰지 마세요.
>
> 💡 앱은 이 폴더부터 위쪽 폴더로 올라가며 `.env`를 찾습니다. 상위 폴더(예: `Wori/.env`)에 이미 있으면 따로 만들지 않아도 됩니다.

---

## ▶️ 실행하기

```bash
conda activate py311
streamlit run app.py
```

브라우저에서 http://localhost:8501 이 자동으로 열립니다. (안 열리면 주소를 직접 입력)

> 💡 `conda activate`가 안 되면 가상환경의 python으로 바로 실행할 수 있습니다.
> ```powershell
> C:\Users\<사용자명>\anaconda3\envs\py311\python.exe -m streamlit run app.py
> ```

종료하려면 터미널에서 **`Ctrl + C`** 를 누릅니다.

---

## 📖 사용법

1. **사이드바**에서 설정을 고릅니다.
   - **HF 모델**: 처음에는 기본값(gemma)을 추천합니다.
   - **설명 길이**: 짧게 / 자세히
   - **한국어 번역**: 켜면 Groq로 번역합니다.
2. 가운데에 **이미지를 끌어다 놓거나** `Browse files`로 선택합니다.
3. **[설명 생성]** 버튼을 누릅니다.
4. 아래에 **English / 한국어** 결과와 사용한 모델·걸린 시간이 나옵니다.

> 같은 이미지·모델·길이로 다시 누르면 API를 다시 부르지 않고 저장된 결과를 보여줍니다. 토큰을 쓰지 않습니다.

---

## 💰 토큰 절약

| 방법 | 설명 |
|---|---|
| 영어 프롬프트 | 시스템 프롬프트와 요청 문장을 **영어**로 작성 (한글은 토큰을 더 많이 씀) |
| 이미지 축소 | 긴 변을 **1024px 이하**로 줄이고 JPEG로 보내서 전송량을 줄임 |
| 결과 캐시 | 같은 요청은 `st.cache_data`로 저장해 다시 호출하지 않음 |
| 번역 추론 low | Groq `gpt-oss`의 `reasoning_effort="low"` → 빠르고 토큰을 적게 씀 |

---

## 🩺 문제 해결

| 증상 | 해결 |
|---|---|
| `.env 에 HF_TOKEN 이 없습니다` | [.env 파일 만들기](#-env-파일-만들기)를 확인 |
| `HF_TOKEN 이 올바르지 않거나 만료됐습니다` | 토큰을 새로 발급해서 `.env`에 다시 넣기 |
| `이번 달 HF 무료 사용량을 모두 썼습니다` | 다음 달까지 기다리거나 HF 결제 설정 확인 |
| `이 모델을 실행해 주는 HF 제공사가 없습니다` | 사이드바에서 다른 모델 선택 |
| `모델이 빈 답변을 보냈습니다` | 다시 시도하거나 다른 모델 선택 |
| 번역 토글이 꺼져서 안 켜짐 | `.env`에 `GROQ_API_KEY`를 넣고 앱 재시작 |
| `번역 실패 : ...` (영어 설명은 나옴) | 안내 문구대로 Groq 키 확인 또는 잠시 후 다시 시도 |
| `서버에 연결할 수 없습니다` | 인터넷 연결 확인 |
| `이미지 파일을 읽을 수 없습니다` | 손상되지 않은 JPG / PNG / WEBP 파일로 다시 올리기 |
| 터미널 한글이 깨짐 (Windows) | PowerShell에서 `[Console]::OutputEncoding = [Text.Encoding]::UTF8` 실행 후 다시 실행 |

---

## 📌 처음 요구사항 (구현 프롬프트)

```
# [HuggingFace 활용해서 깃허브 레포 새롭게 구축]
# 1. 원하는 모델 선정 --> image-to-text(https://huggingface.co/models?pipeline_tag=image-to-text&sort=trending)
# 2. 간단한 서비스 개발
# 3. 깃허브 레포 생성(261020_bucheon_huggingface_이름이니셜)
# 4. 레포명 : https://github.com/Youkjooyoung/261020_bucheon_huggingface_yjy.git
# 5. 작업 폴더 경로 : wori/261020_8_hugging/261020_bucheon_hugging_yjy/

# - claude 활용하여 로컬 형태 수준 혹은 자유롭게 개발
# - env 관리 점검
# - requirements.txt 생성 필수(필요 라이브러리 목록 확인)
# - README.md 사용법 작성 필수
# - 시스템 프롬프트는 영어로 구현 (한글은 토큰을 많이 먹음)
```
