import streamlit as st
import httpx
import json

# Page config 
st.set_page_config(
    page_title="Medical Assistant",
    page_icon = "⚕️",
    layout="wide",
    initial_sidebar_state='expanded'
)


# Custom CSS for premium look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background-color:  #11746f;
    }
    
    .stApp {
        #background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        background-color: #1e1e2f;  /* dark theme */
    }
    
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        background-color: #007bff;
        color: white;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #0056b3;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .sidebar .sidebar-content {
        background-color: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
    }
    
    .source-tag {
        display: inline-block;
        padding: 2px 8px;
        margin: 2px;
        background-color: #e9ecef;
        border-radius: 12px;
        font-size: 0.8rem;
        color: #495057;
    }
    
    h1 {
        color: #1a1a1a;
        font-weight: 600;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/medical-doctor.png", width=80)
    st.title("MedAssist AI")
    st.markdown("---")
    st.markdown("### 📥 Data Ingestion")

    if st.button("Ingest Documents"):
        with st.spinner("Ingesting documents..."):
            try:
                with httpx.Client() as client:
                    response = client.post("http://localhost:8000/ingest", timeout=60.0)

                    if response.status_code == 200:
                        st.success("✅ Ingestion completed successfully!")
                    else:
                        st.error(f"❌ Error: {response.text}")
            except Exception as e:
                st.error(f"❌ Failed to connect: {str(e)}")

    st.markdown("---")
    st.markdown("### About")
    st.write("An advanced RAG-based assistant for searching and analyzing medical literature.")
    st.markdown("### Features")
    st.markdown("- ⚡ Low Latency\n- 📚 Source Verification\n- 🔍 Semantic Search")
    st.markdown("---")
    if st.button("Clear Chat"):
        st.session_state.messages = []


# ---------------- MAIN UI ----------------
# Main Title
st.markdown("<h1>⚕️ Medical Literature Assistant</h1>", unsafe_allow_html=True)

# Chat logic
if 'messages' not in st.session_state:
    st.session_state.messages = []


# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        if 'sources' in message:
            st.markdown("---")
            st.markdown("**Sources:**")
            for src in message['sources']:
                st.markdown(f"<span class='source-tag'>{src}</span>", unsafe_allow_html=True)


# Chat input
if prompt := st.chat_input("Ask a medical question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)


    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Searching literature...")


        try:
            # Call backend
            with httpx.Client() as client:
                response = client.post("http://localhost:8000/query", json={"query": prompt}, timeout=30.0)
                if response.status_code == 200:
                    data = response.json()
                    answer = data['answer']
                    sources = data['sources']

                    message_placeholder.markdown(answer)
                    message_placeholder.markdown(answer)
                    st.markdown("---")
                    st.markdown("**Sources:**")
                    for src in sources:
                        st.markdown(f"<span class='source-tag'>{src}</span>", unsafe_allow_html=True)
                    
                    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
                else:
                    message_placeholder.error(f"Error: {response.text}")
        except Exception as e:
            message_placeholder.error(f"Failed to connect to backend: {str(e)}")