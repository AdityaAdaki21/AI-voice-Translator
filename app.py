import os
import time
import pygame
import streamlit as st
import speech_recognition as sr
from googletrans import LANGUAGES, Translator
from gtts import gTTS
from io import BytesIO

# Configure Streamlit page
st.set_page_config(
    page_title="🌍 Real-Time Voice Translator", 
    page_icon="🗣️", 
    layout="wide"
)

# Initialize key session state variables
if 'is_translating' not in st.session_state:
    st.session_state.is_translating = False
if 'status' not in st.session_state:
    st.session_state.status = "Ready to translate"
if 'translated_text' not in st.session_state:
    st.session_state.translated_text = ""
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Initialize translator
translator = Translator()
pygame.mixer.init()

# Language mapping
language_mapping = {name: code for code, name in LANGUAGES.items()}

def get_language_code(language_name):
    """Convert language name to language code."""
    return language_mapping.get(language_name, language_name)

def translate_text(text, from_lang, to_lang):
    """Translate text between languages."""
    try:
        return translator.translate(text, src=from_lang, dest=to_lang)
    except Exception as e:
        st.error(f"Translation error: {e}")
        return None

def text_to_speech(text, lang):
    """Convert text to speech."""
    try:
        with BytesIO() as f:
            gTTS(text=text, lang=lang, slow=False).write_to_fp(f)
            f.seek(0)
            pygame.mixer.music.load(f)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
    except Exception as e:
        st.error(f"Text-to-Speech error: {e}")

def translate_and_speak():
    """Core translation function."""
    # Reset translation status
    st.session_state.status = "🎙️ Preparing to listen..."
    
    # Initialize recognizer
    recognizer = sr.Recognizer()
    
    try:
        # Use microphone
        with sr.Microphone() as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # Update status
            st.session_state.status = "🎙️ Listening..."
            
            # Listen for speech
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            
            # Update status
            st.session_state.status = "🔄 Processing speech..."
            
            # Recognize speech
            try:
                spoken_text = recognizer.recognize_google(
                    audio, 
                    language=st.session_state.current_from_lang
                )
            except sr.UnknownValueError:
                st.session_state.status = "❓ Could not understand audio"
                return
            except sr.RequestError:
                st.session_state.status = "❌ Speech recognition error"
                return
            
            # Translate
            st.session_state.status = "✨ Translating..."
            translation = translate_text(
                spoken_text, 
                st.session_state.current_from_lang, 
                st.session_state.current_to_lang
            )
            
            if translation:
                # Prepare translation text
                translated_text = translation.text
                
                # Update translated text
                st.session_state.translated_text = (
                    f"Original ({st.session_state.current_from_lang}): {spoken_text}\n"
                    f"Translation ({st.session_state.current_to_lang}): {translated_text}"
                )
                
                # Add to conversation history
                st.session_state.conversation_history.append({
                    'original': spoken_text,
                    'translation': translated_text,
                    'from_lang': st.session_state.current_from_lang,
                    'to_lang': st.session_state.current_to_lang
                })
                
                # Text to speech
                text_to_speech(translated_text, st.session_state.current_to_lang)
                
                # Update status
                st.session_state.status = "✅ Translation complete"
            
    except Exception as e:
        st.session_state.status = f"❌ Error: {e}"
    finally:
        # Ensure translation is stopped
        st.session_state.is_translating = False

def main():
    # Title and description
    st.title("🌍 Real-Time Voice Translator")
    st.markdown("""
        ### Instant Speech Translation
        Speak in one language, hear the translation instantly!
    """)

    # Sidebar language selection
    st.sidebar.header("🌐 Translation Settings")
    from_lang_name = st.sidebar.selectbox(
        "Source Language",
        sorted(LANGUAGES.values()),
        format_func=lambda x: f"{x} ({language_mapping[x].upper()})",
        help="Select the language you will speak in",
        key="from_lang_select"
    )
    to_lang_name = st.sidebar.selectbox(
        "Target Language",
        sorted(LANGUAGES.values()),
        format_func=lambda x: f"{x} ({language_mapping[x].upper()})",
        help="Select the language you want to translate to",
        key="to_lang_select"
    )

    # Get language codes
    st.session_state.current_from_lang = get_language_code(from_lang_name)
    st.session_state.current_to_lang = get_language_code(to_lang_name)

    # Translation controls
    col1, col2 = st.columns(2)
    with col1:
        start_button = st.button(
            "🎙️ Start Listening", 
            use_container_width=True,
            key="start_translation"
        )
        if start_button:
            st.session_state.is_translating = True
            translate_and_speak()

    with col2:
        stop_button = st.button(
            "🛑 Stop Listening", 
            use_container_width=True,
            key="stop_translation"
        )
        if stop_button:
            st.session_state.is_translating = False
            st.session_state.status = "🛑 Stopped"

    # Status display
    st.markdown(f"### 📡 Status: {st.session_state.status}")

    # Translation output
    st.markdown("### 💬 Translation")
    if st.session_state.translated_text:
        st.info(st.session_state.translated_text)
    else:
        st.info("Translation will appear here")

    # Conversation history
    st.markdown("### 📜 Conversation History")
    if st.session_state.conversation_history:
        for entry in reversed(st.session_state.conversation_history[-5:]):
            st.markdown(f"""
            - **Original ({entry['from_lang']})**: {entry['original']}
            - **Translation ({entry['to_lang']})**: {entry['translation']}
            """)
    else:
        st.info("Your translation history will be saved here")

    # Sidebar tips
    st.sidebar.markdown("### 💡 Tips")
    st.sidebar.info("""
    - Speak clearly into the microphone
    - Choose source and target languages carefully
    - Stop and restart if translation isn't accurate
    """)

if __name__ == "__main__":
    main()