"""Multilingual translation service supporting legal-aid tenant intake."""

from typing import Dict, Optional
import os

SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish (Español)",
    "zh": "Chinese (中文)",
    "bn": "Bengali (বাংলা)",
    "ht": "Haitian Creole (Kreyòl Ayisyen)",
}

# Offline phrasebook for critical legal-aid intake terms and guidance
COMMON_PHRASES: Dict[str, Dict[str, str]] = {
    "es": {
        "welcome": "Bienvenido/a. Estamos aquí para ayudarle con su caso de vivienda y corte.",
        "ask_address": "¿En qué cuadra o vecindario vive usted?",
        "ask_hearing": "¿Tiene una fecha de audiencia en la corte o un número de caso?",
        "ask_hazards": "¿Qué problemas tiene en su apartamento? (calefacción, goteras, moho, agua caliente)",
        "ask_arrears": "¿Cuánto dinero dice el propietario que le debe en renta?",
        "reassurance": "La ley de Nueva York protege su derecho a una vivienda habitable. Si no tiene calefacción o tiene moho, podemos solicitar una reducción de renta y ayuda financiera.",
        "court_warning": "Es muy importante que asista a su audiencia en la corte para evitar una orden de desalojo en rebeldía.",
    },
    "zh": {
        "welcome": "欢迎。我们在这里帮助您处理住房和法庭案件。",
        "ask_address": "请问您住在哪个街区或附近？",
        "ask_hearing": "您有出庭日期或法院案号吗？",
        "ask_hazards": "您的公寓有什么问题？（暖气、漏水、黑霉、热水）",
        "ask_arrears": "房东称您欠多少房租？",
        "reassurance": "纽约法律保护您的宜居权。如果没有暖气或有霉菌，我们可以申请减租和紧急租金补助。",
        "court_warning": "您必须出庭，以避免法院做出缺席判决。",
    },
    "ht": {
        "welcome": "Byenveni. Nou la pou ede w ak ka lojman w ak tribinal.",
        "ask_address": "Nan ki blòk oswa katye w ap viv?",
        "ask_hearing": "Èske w gen yon dat tribinal oswa yon nimewo ka?",
        "ask_hazards": "Ki pwoblèm ou genyen nan apatman w lan? (chofaj, dlo k ap koule, mwazi, dlo cho)",
        "ask_arrears": "Konbyen lajan pwopriyetè a di ou dwe nan lwaye?",
        "reassurance": "Lalwa pwoteje dwa w pou gen yon kay ki ka viv ladan l. Nou ka ede w mande asistans lwaye ijan.",
        "court_warning": "Li trè enpòtan pou w ale nan tribinal pou evite yo jije w pa defo.",
    },
}


def translate_text(
    text: str,
    target_lang: str = "en",
    source_lang: Optional[str] = None,
) -> str:
    """Translate text between English and tenant languages using Gemini if available, or phrasebook."""
    if not text or target_lang == source_lang or (target_lang == "en" and source_lang == "en"):
        return text

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            target_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)
            prompt = (
                f"You are a compassionate legal-aid housing intake assistant. "
                f"Translate the following tenant intake message into {target_name}. "
                f"Maintain legal accuracy, clear respectful language, and do not add commentary:\n\n{text}"
            )
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()
        except Exception:
            pass

    # Offline translation fallback for common prompts
    lang_key = target_lang[:2].lower()
    if lang_key in COMMON_PHRASES:
        for phrase_id, translation in COMMON_PHRASES[lang_key].items():
            if phrase_id in text.lower():
                return translation

    # Return original with language indicator if offline
    if target_lang != "en":
        return f"[{SUPPORTED_LANGUAGES.get(target_lang, target_lang)}] {text}"
    return text
