import os
import time

import streamlit as st
from dotenv import load_dotenv, find_dotenv

import hf

# 1. .env 불러오기 (이 폴더부터 위로 올라가며 찾음 -> 없으면 Wori 루트의 .env 사용)
load_dotenv(find_dotenv())

st.set_page_config(page_title="Image Captioner", page_icon=":material/image_search:")
st.title(":material/image_search: 이미지 설명 생성기")
st.caption("Hugging Face 모델이 이미지를 보고 설명을 써 주고, Groq 가 한국어로 번역합니다.")


# 2. 같은 이미지·모델·스타일이면 API 를 다시 부르지 않음 (캐시 -> 토큰 절약)
#    걸린 시간도 같이 저장 -> 캐시에서 꺼내도 처음 걸린 시간이 보임
@st.cache_data(show_spinner=False)
def cached_describe(image_bytes, model, style):
    start = time.time()
    caption = hf.describe(image_bytes, model, style)
    return caption, time.time() - start


@st.cache_data(show_spinner=False)
def cached_translate(text):
    return hf.translate_ko(text)


# 3. 사이드바 : 설정
with st.sidebar:
    st.header("설정")
    model = st.selectbox("HF 모델", hf.HF_MODELS)
    style = st.radio("설명 길이", list(hf.STYLES))
    has_groq = bool(os.getenv("GROQ_API_KEY"))
    translate = st.toggle("한국어 번역 (Groq)", value=has_groq, disabled=not has_groq)
    if not has_groq:
        st.caption(".env 에 GROQ_API_KEY 가 없어서 번역을 쓸 수 없습니다.")

if not os.getenv("HF_TOKEN"):
    st.error(".env 에 HF_TOKEN 이 없습니다. README 의 '.env 파일 만들기' 를 참고해 넣어주세요.", icon=":material/key_off:")
    st.stop()


# 4. 이미지 올리기
uploaded = st.file_uploader("이미지를 올려주세요", type=["jpg", "jpeg", "png", "webp"])
if uploaded is None:
    st.info("JPG / PNG / WEBP 이미지를 끌어다 놓거나 'Browse files' 를 누르세요.", icon=":material/upload:")
    st.stop()

image_bytes = uploaded.getvalue()
st.image(image_bytes, caption=uploaded.name, width="stretch")


# 5. 설명 생성 -> 결과는 session_state 에 저장 (설정을 바꿔도 화면에 남도록)
if st.button("설명 생성", type="primary", icon=":material/auto_awesome:"):
    st.session_state.pop("result", None)
    try:
        with st.spinner(f"{model} 이(가) 이미지를 보는 중..."):
            caption, seconds = cached_describe(image_bytes, model, style)
    except Exception as e:
        st.error(hf.error_message(e), icon=":material/error:")
    else:
        # 5-1. 번역은 따로 처리 -> 번역이 실패해도 영어 설명은 보여줌
        korean = None
        if translate:
            try:
                with st.spinner("한국어로 번역하는 중..."):
                    korean = cached_translate(caption)
            except Exception as e:
                st.warning(f"번역 실패 : {hf.error_message(e)}", icon=":material/translate:")
        st.session_state.result = {
            "file_id": uploaded.file_id, "model": model,
            "caption": caption, "korean": korean, "seconds": seconds,
        }


# 6. 결과 보여주기 (지금 올린 이미지의 결과일 때만)
result = st.session_state.get("result")
if result and result["file_id"] == uploaded.file_id:
    st.subheader("결과")
    st.markdown("**English**")
    st.write(result["caption"])
    if result["korean"]:
        st.markdown("**한국어**")
        st.write(result["korean"])
    st.caption(f"{result['model']} · {result['seconds']:.1f}초")
