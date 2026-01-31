import streamlit as st
import os
import tempfile
from brain import setup_agent, ask_agent

st.set_page_config(page_title="Agentic RAG Assistant", layout = "wide", page_icon = "🤖")

st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Ukrycie napisu Deploy */
    [data-testid="stToolbar"] {
        display: none;
    }
    
    /* Logo w lewym górnym rogu */
    .app-logo {
        position: fixed;
        top: 20px;
        left: 20px;
        font-size: 30px;
        font-weight: 700;
        color: #FAFAFA;
        z-index: 999;
    }

    .main-title {
        text-align: center;
        font-size: 3.5rem;
        font-weight: 700;
        margin-top: 0.5rem;
        margin-bottom: 2rem;
    }
    .sub-title {
        text-align: center;
        color: #9CA3AF;
        font-size: 1.8rem;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    
    .bot-icon-container {
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    div[data-testid = "stFileUploader"] {
        background-color: #1A1C24;
        padding: 3rem;
        border-radius: 20px;
        border: 2px dashed #374151;
        transition: border 0.3s;
    }
    
    /* Ukrycie sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Maksymalne usunięcie paddingu na stronie czatu */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* Landing page - obniżony */
    .landing-container {
        padding-top: 15vh;
    }
    
    /* Przycisk New Chat na samej górze */
    .new-chat-fixed {
        position: fixed;
        top: 15px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 998;
        width: 300px;
    }
</style>
""", unsafe_allow_html = True)

# Logo w lewym górnym rogu - wyświetlane zawsze
st.markdown("<div class='app-logo'>Agentic RAG Assistant</div>", unsafe_allow_html=True)

if "agent_executor" not in st.session_state:
    st.session_state.agent_executor = None
if "messages" not in st.session_state:
    st.session_state.messages = []

if st.session_state.agent_executor is None:
    # Landing page - obniżona zawartość
    st.markdown("<div class='landing-container'>", unsafe_allow_html=True)
    st.markdown("<div class='bot-icon-container'> <img src = 'https://cdn-icons-png.flaticon.com/512/4712/4712035.png' width = '100'> </div>", unsafe_allow_html = True)
    st.markdown("<div class = 'sub-title'> Hi, there! </div>", unsafe_allow_html = True)
    st.markdown("<div class = 'main-title'> Upload your PDF file </div>", unsafe_allow_html = True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        uploaded_file = st.file_uploader("Upload PDF file", type = "pdf", label_visibility = "collapsed")

        if uploaded_file:
            
            file_path = None

            try:
                with tempfile.NamedTemporaryFile(delete = False, suffix = ".pdf") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        file_path = tmp.name
            except Exception as e:
                st.error(f"Can't save file: {e}")

            if file_path is not None: 
                with st.spinner("Analyzing document..."):
                    try:
                       executor = setup_agent(file_path)
                       st.session_state.agent_executor = executor

                       st.session_state.messages.append({"role": "assistant", "content": "I've analyzed document. How can I help you today?"})
                       st.rerun()
                    except Exception as e:
                        st.error(f"Error during setup: {e}")
            else:
                    st.error("Error: can't create a temporary path. ")
    
    st.markdown("</div>", unsafe_allow_html=True)

else:
    # Strona czatu - przycisk New Chat fixed na górze
    st.markdown("""
    <div class='new-chat-fixed'>
        <form action="" method="get">
            <button type="submit" name="new_chat" style="
                width: 100%;
                padding: 0.5rem;
                background-color: #1A1C24;
                color: #FAFAFA;
                border: 1px solid #374151;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
            ">🔄 New Chat</button>
        </form>
    </div>
    """, unsafe_allow_html=True)
    
    # Sprawdzenie czy przycisk został kliknięty
    if st.query_params.get("new_chat"):
        st.session_state.agent_executor = None
        st.session_state.messages = []
        st.query_params.clear()
        st.rerun()
    
    # Dodanie paddingu żeby czat nie nachodzi na przycisk
    st.markdown("<div style='padding-top: 60px;'></div>", unsafe_allow_html=True)
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    if prompt := st.chat_input("Ask me anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = ask_agent(st.session_state.agent_executor, prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
