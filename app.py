import os
import time
import streamlit as st
import speech_recognition as sr
from googletrans import LANGUAGES, Translator
from io import BytesIO
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configure Streamlit page with custom theme and layout
st.set_page_config(
    page_title="🌎 Voice Translator Pro", 
    page_icon="🗣️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
    }
    .subheader {
        font-size: 1.5rem;
        color: #424242;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-ready {
        color: green;
        font-weight: bold;
    }
    .status-listening {
        color: blue;
        font-weight: bold;
        animation: pulse 1.5s infinite;
    }
    .status-processing {
        color: orange;
        font-weight: bold;
    }
    .status-error {
        color: red;
        font-weight: bold;
    }
    .card {
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .card-header {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    .stButton>button {
        font-weight: bold;
        height: 3rem;
    }
    .language-info {
        font-size: 0.9rem;
        color: #616161;
    }
    .stats-container {
        background-color: #f5f5f5;
        border-radius: 10px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'app_state' not in st.session_state:
    st.session_state.app_state = {
        'is_translating': False,
        'status': "Ready to translate",
        'status_class': "status-ready",
        'translated_text': "",
        'conversation_history': [],
        'start_time': datetime.now(),
        'total_translations': 0,
        'favorites': [],
        'settings': {
            'max_history': 10,
            'speech_timeout': 5,
            'theme': 'light',
            'show_stats': True
        }
    }

# Initialize translator
translator = Translator()

# Language mapping
language_mapping = {name: code for code, name in LANGUAGES.items()}
language_code_to_name = {code: name for name, code in language_mapping.items()}

# Language popularity (for better default selections)
popular_languages = ["english", "spanish", "french", "german", "chinese", "japanese", "russian", "arabic"]

def get_language_code(language_name):
    """Convert language name to language code."""
    return language_mapping.get(language_name.lower(), language_name)

def get_language_name(language_code):
    """Convert language code to language name."""
    return language_code_to_name.get(language_code, language_code).capitalize()

def update_status(status, status_class):
    """Update status with proper styling."""
    st.session_state.app_state['status'] = status
    st.session_state.app_state['status_class'] = status_class

def translate_text(text, from_lang, to_lang):
    """Translate text between languages with error handling."""
    if not text.strip():
        return None
        
    try:
        result = translator.translate(text, src=from_lang, dest=to_lang)
        st.session_state.app_state['total_translations'] += 1
        return result
    except Exception as e:
        st.error(f"Translation error: {e}")
        update_status(f"❌ Translation failed: {e}", "status-error")
        return None

def save_to_favorites():
    """Save current translation to favorites."""
    if st.session_state.app_state['translated_text']:
        st.session_state.app_state['favorites'].append(
            st.session_state.app_state['conversation_history'][-1]
        )
        st.success("Added to favorites!")

def export_history():
    """Export conversation history to CSV."""
    if st.session_state.app_state['conversation_history']:
        df = pd.DataFrame(st.session_state.app_state['conversation_history'])
        return df.to_csv(index=False).encode('utf-8')
    return None

def translate_speech():
    """Core translation function with improved error handling."""
    # Reset translation status
    update_status("🎙️ Preparing to listen...", "status-processing")
    
    # Initialize recognizer
    recognizer = sr.Recognizer()
    
    try:
        # Use microphone
        with sr.Microphone() as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # Update status
            update_status("🎙️ Listening...", "status-listening")
            
            # Listen for speech
            audio = recognizer.listen(
                source, 
                timeout=st.session_state.app_state['settings']['speech_timeout'],
                phrase_time_limit=st.session_state.app_state['settings']['speech_timeout']
            )
            
            # Update status
            update_status("🔄 Processing speech...", "status-processing")
            
            # Recognize speech
            try:
                spoken_text = recognizer.recognize_google(
                    audio, 
                    language=st.session_state.current_from_lang
                )
            except sr.UnknownValueError:
                update_status("❓ Could not understand audio", "status-error")
                return
            except sr.RequestError:
                update_status("❌ Speech recognition service unavailable", "status-error")
                return
            
            # Translate
            update_status("✨ Translating...", "status-processing")
            
            # Add timestamp for history tracking
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            translation = translate_text(
                spoken_text, 
                st.session_state.current_from_lang, 
                st.session_state.current_to_lang
            )
            
            if translation:
                # Prepare translation text
                translated_text = translation.text
                
                # Update translated text
                st.session_state.app_state['translated_text'] = {
                    'original': spoken_text,
                    'translation': translated_text,
                    'from_lang': get_language_name(st.session_state.current_from_lang),
                    'to_lang': get_language_name(st.session_state.current_to_lang)
                }
                
                # Add to conversation history
                history_entry = {
                    'timestamp': timestamp,
                    'original': spoken_text,
                    'translation': translated_text,
                    'from_lang': st.session_state.current_from_lang,
                    'to_lang': st.session_state.current_to_lang,
                    'from_lang_name': get_language_name(st.session_state.current_from_lang),
                    'to_lang_name': get_language_name(st.session_state.current_to_lang)
                }
                
                st.session_state.app_state['conversation_history'].append(history_entry)
                
                # Limit history to max_history entries
                if len(st.session_state.app_state['conversation_history']) > st.session_state.app_state['settings']['max_history']:
                    st.session_state.app_state['conversation_history'] = st.session_state.app_state['conversation_history'][-st.session_state.app_state['settings']['max_history']:]
                
                # Update status
                update_status("✅ Translation complete", "status-ready")
            
    except Exception as e:
        update_status(f"❌ Error: {str(e)}", "status-error")
    finally:
        # Ensure translation is stopped
        st.session_state.app_state['is_translating'] = False

def text_input_translation():
    """Handle manual text input translation."""
    input_text = st.session_state.text_input
    if not input_text:
        return
        
    update_status("✨ Translating...", "status-processing")
    
    # Add timestamp for history tracking
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    translation = translate_text(
        input_text, 
        st.session_state.current_from_lang, 
        st.session_state.current_to_lang
    )
    
    if translation:
        # Prepare translation text
        translated_text = translation.text
        
        # Update translated text
        st.session_state.app_state['translated_text'] = {
            'original': input_text,
            'translation': translated_text,
            'from_lang': get_language_name(st.session_state.current_from_lang),
            'to_lang': get_language_name(st.session_state.current_to_lang)
        }
        
        # Add to conversation history
        history_entry = {
            'timestamp': timestamp,
            'original': input_text,
            'translation': translated_text,
            'from_lang': st.session_state.current_from_lang,
            'to_lang': st.session_state.current_to_lang,
            'from_lang_name': get_language_name(st.session_state.current_from_lang),
            'to_lang_name': get_language_name(st.session_state.current_to_lang),
            'input_type': 'text'
        }
        
        st.session_state.app_state['conversation_history'].append(history_entry)
        
        # Limit history to max_history entries
        if len(st.session_state.app_state['conversation_history']) > st.session_state.app_state['settings']['max_history']:
            st.session_state.app_state['conversation_history'] = st.session_state.app_state['conversation_history'][-st.session_state.app_state['settings']['max_history']:]
        
        # Clear the input field
        st.session_state.text_input = ""
        
        # Update status
        update_status("✅ Translation complete", "status-ready")

def display_stats():
    """Display usage statistics."""
    if not st.session_state.app_state['settings']['show_stats']:
        return
        
    st.markdown("### 📊 Usage Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Translations", 
            st.session_state.app_state['total_translations']
        )
    
    with col2:
        # Calculate app uptime
        uptime = datetime.now() - st.session_state.app_state['start_time']
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        uptime_str = f"{hours}h {minutes}m"
        st.metric("Session Duration", uptime_str)
    
    with col3:
        if st.session_state.app_state['conversation_history']:
            langs = {}
            for entry in st.session_state.app_state['conversation_history']:
                target = entry['to_lang_name']
                langs[target] = langs.get(target, 0) + 1
            most_used = max(langs, key=langs.get)
            st.metric("Most Used Language", most_used)
        else:
            st.metric("Most Used Language", "None")
    
    # Language usage chart
    if st.session_state.app_state['conversation_history']:
        lang_counts = {}
        for entry in st.session_state.app_state['conversation_history']:
            target = entry['to_lang_name']
            lang_counts[target] = lang_counts.get(target, 0) + 1
        
        # Create DataFrame for chart
        chart_data = pd.DataFrame({
            'Language': list(lang_counts.keys()),
            'Count': list(lang_counts.values())
        })
        
        # Create and display chart
        fig = px.bar(
            chart_data, 
            x='Language', 
            y='Count', 
            title='Target Language Usage',
            color='Count',
            color_continuous_scale='blues'
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

def main():
    # Set up tabs for different app sections
    tabs = st.tabs(["🔤 Translator", "📜 History", "⚙️ Settings"])
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("<h2 style='text-align: center;'>🌎 Voice Translator Pro</h2>", unsafe_allow_html=True)
        st.image("https://cdn.pixabay.com/photo/2013/07/13/01/22/world-155534_960_720.png", use_column_width=True)
        
        st.markdown("### 🌐 Language Settings")
        
        # Source language with popular options first
        all_languages = sorted(LANGUAGES.values())
        default_from_index = all_languages.index("english") if "english" in all_languages else 0
        
        from_lang_name = st.selectbox(
            "Source Language",
            all_languages,
            index=default_from_index,
            format_func=lambda x: f"{x.capitalize()} ({language_mapping[x].upper()})",
            help="Select the language you will speak in",
            key="from_lang_select"
        )
        
        # Target language with popular options first
        default_to_index = all_languages.index("spanish") if "spanish" in all_languages else 0
        if default_to_index == default_from_index:
            default_to_index = (default_to_index + 1) % len(all_languages)
            
        to_lang_name = st.selectbox(
            "Target Language",
            all_languages,
            index=default_to_index,
            format_func=lambda x: f"{x.capitalize()} ({language_mapping[x].upper()})",
            help="Select the language you want to translate to",
            key="to_lang_select"
        )
        
        # Quick language swap button
        if st.button("🔄 Swap Languages", use_container_width=True):
            # Store current values
            temp_from = st.session_state.from_lang_select
            temp_to = st.session_state.to_lang_select
            
            # Swap values
            st.session_state.from_lang_select = temp_to
            st.session_state.to_lang_select = temp_from
            
            # Force rerun to update UI
            st.experimental_rerun()
    
        # Get language codes
        st.session_state.current_from_lang = get_language_code(from_lang_name)
        st.session_state.current_to_lang = get_language_code(to_lang_name)
        
        # Tips and Help
        with st.expander("💡 Tips & Help"):
            st.markdown("""
            - Speak clearly into the microphone
            - Keep background noise to a minimum
            - For longer sentences, pause naturally
            - Use the text input for manual translation
            - Save important translations to favorites
            - Export history for your records
            """)
        
        # About section
        with st.expander("ℹ️ About"):
            st.markdown("""
            **Voice Translator Pro** lets you translate between 100+ languages using your voice or text input.
            
            Built with Streamlit, SpeechRecognition, and Google Translate API.
            
            Version 2.0
            """)
            
    # Get language codes
    st.session_state.current_from_lang = get_language_code(from_lang_name)
    st.session_state.current_to_lang = get_language_code(to_lang_name)
    
    # Main translator tab
    with tabs[0]:
        # App header
        st.markdown("<h1 class='main-header'>Voice Translator Pro</h1>", unsafe_allow_html=True)
        st.markdown("<p class='subheader'>Speak or type in one language, get instant translation</p>", unsafe_allow_html=True)
        
        # Display current language configuration
        lang_col1, lang_col2 = st.columns(2)
        with lang_col1:
            st.markdown(f"<p class='language-info'>From: <b>{get_language_name(st.session_state.current_from_lang)}</b> ({st.session_state.current_from_lang})</p>", unsafe_allow_html=True)
        with lang_col2:
            st.markdown(f"<p class='language-info'>To: <b>{get_language_name(st.session_state.current_to_lang)}</b> ({st.session_state.current_to_lang})</p>", unsafe_allow_html=True)
        
        # Status indicator
        st.markdown(f"<h3>📡 Status: <span class='{st.session_state.app_state['status_class']}'>{st.session_state.app_state['status']}</span></h3>", unsafe_allow_html=True)
        
        # Translation controls
        st.markdown("### 🎙️ Speech Input")
        col1, col2 = st.columns(2)
        with col1:
            start_button = st.button(
                "🎙️ Start Listening", 
                use_container_width=True,
                key="start_translation"
            )
            if start_button:
                st.session_state.app_state['is_translating'] = True
                translate_speech()

        with col2:
            stop_button = st.button(
                "🛑 Stop Listening", 
                use_container_width=True,
                key="stop_translation"
            )
            if stop_button:
                st.session_state.app_state['is_translating'] = False
                update_status("🛑 Stopped", "status-ready")
        
        # Text input alternative
        st.markdown("### ⌨️ Text Input")
        text_col1, text_col2 = st.columns([3, 1])
        with text_col1:
            st.text_area(
                "Or type text to translate",
                key="text_input",
                placeholder="Type here and press Translate...",
                height=100
            )
        with text_col2:
            translate_button = st.button(
                "✨ Translate Text", 
                use_container_width=True,
                key="translate_text"
            )
            if translate_button:
                text_input_translation()
                
        # Translation output
        st.markdown("### 💬 Translation Results")
        if st.session_state.app_state['translated_text']:
            result = st.session_state.app_state['translated_text']
            
            # Create two columns for the cards
            res_col1, res_col2 = st.columns(2)
            
            with res_col1:
                st.markdown(f"""
                <div class='card'>
                    <div class='card-header'>Original ({result['from_lang']})</div>
                    <div>{result['original']}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with res_col2:
                st.markdown(f"""
                <div class='card'>
                    <div class='card-header'>Translation ({result['to_lang']})</div>
                    <div>{result['translation']}</div>
                </div>
                """, unsafe_allow_html=True)
                
            # Quick actions for the current translation
            action_col1, action_col2 = st.columns(2)
            
            with action_col1:
                if st.button("⭐ Save to Favorites", use_container_width=True):
                    save_to_favorites()
                    
            with action_col2:
                if st.button("🔄 New Translation", use_container_width=True):
                    st.session_state.app_state['translated_text'] = ""
                    update_status("Ready to translate", "status-ready")
        else:
            st.info("Translation results will appear here")
    
    # History tab
    with tabs[1]:
        st.markdown("## 📜 Translation History")
        
        # History controls
        hist_col1, hist_col2 = st.columns([3, 1])
        
        with hist_col2:
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.app_state['conversation_history'] = []
                st.success("History cleared!")
            
            if st.session_state.app_state['conversation_history'] and st.download_button(
                "📥 Export to CSV",
                export_history(),
                "translation_history.csv",
                "text/csv",
                use_container_width=True
            ):
                st.success("History exported!")
        
        with hist_col1:
            # Search in history
            search_term = st.text_input("🔍 Search in history", placeholder="Enter text to search...")
        
        # Favorites section
        if st.session_state.app_state['favorites']:
            with st.expander("⭐ Favorites", expanded=True):
                for i, entry in enumerate(reversed(st.session_state.app_state['favorites'])):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Original ({get_language_name(entry['from_lang'])})**: {entry['original']}")
                    with col2:
                        st.markdown(f"**Translation ({get_language_name(entry['to_lang'])})**: {entry['translation']}")
                    st.divider()
        
        # Main history list
        if st.session_state.app_state['conversation_history']:
            filtered_history = st.session_state.app_state['conversation_history']
            
            # Apply search filter if needed
            if search_term:
                filtered_history = [
                    entry for entry in filtered_history 
                    if search_term.lower() in entry['original'].lower() or 
                       search_term.lower() in entry['translation'].lower()
                ]
            
            for i, entry in enumerate(reversed(filtered_history)):
                # Format timestamp
                time_str = entry.get('timestamp', 'Unknown time')
                
                # Create expandable entry
                with st.expander(f"Entry {len(filtered_history)-i}: {time_str}", expanded=(i==0)):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Original ({entry['from_lang_name']})**: {entry['original']}")
                    with col2:
                        st.markdown(f"**Translation ({entry['to_lang_name']})**: {entry['translation']}")
                    
                    # Add to favorites button
                    if st.button(f"⭐ Add to Favorites", key=f"fav_{i}", use_container_width=True):
                        if entry not in st.session_state.app_state['favorites']:
                            st.session_state.app_state['favorites'].append(entry)
                            st.success("Added to favorites!")
        else:
            st.info("Your translation history will appear here")
        
        # Display usage statistics
        display_stats()
    
    # Settings tab
    with tabs[2]:
        st.markdown("## ⚙️ Settings")
        
        # Settings Columns
        set_col1, set_col2 = st.columns(2)
        
        with set_col1:
            # Max history setting
            st.number_input(
                "Maximum History Entries",
                min_value=5,
                max_value=100,
                value=st.session_state.app_state['settings']['max_history'],
                step=5,
                help="Set the maximum number of translations to keep in history",
                key="max_history_setting"
            )
            st.session_state.app_state['settings']['max_history'] = st.session_state.max_history_setting
            
            # Speech timeout setting
            st.number_input(
                "Speech Recognition Timeout (seconds)",
                min_value=1,
                max_value=15,
                value=st.session_state.app_state['settings']['speech_timeout'],
                step=1,
                help="Set how long to listen for speech before timing out",
                key="speech_timeout_setting"
            )
            st.session_state.app_state['settings']['speech_timeout'] = st.session_state.speech_timeout_setting
        
        with set_col2:
            # Theme selection
            theme = st.selectbox(
                "App Theme",
                ["Light", "Dark"],
                index=0 if st.session_state.app_state['settings']['theme'] == 'light' else 1,
                help="Select app color theme (requires page refresh)",
                key="theme_setting"
            )
            st.session_state.app_state['settings']['theme'] = theme.lower()
            
            # Show/hide statistics
            show_stats = st.checkbox(
                "Show Statistics",
                value=st.session_state.app_state['settings']['show_stats'],
                help="Show or hide usage statistics on the History tab",
                key="show_stats_setting"
            )
            st.session_state.app_state['settings']['show_stats'] = show_stats
        
        # Reset all settings button
        if st.button("Reset All Settings to Default", use_container_width=True):
            st.session_state.app_state['settings'] = {
                'max_history': 10,
                'speech_timeout': 5,
                'theme': 'light',
                'show_stats': True
            }
            st.success("Settings have been reset to default values!")
            st.experimental_rerun()

if __name__ == "__main__":
    main()