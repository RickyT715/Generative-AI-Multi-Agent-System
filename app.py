"""Streamlit UI for the AI Customer Support Assistant."""

import os
import tempfile
import uuid

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AI Customer Support Assistant",
    page_icon="🤖",
    layout="wide",
)


# --- Session State Initialization ---
def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    if "last_agent" not in st.session_state:
        st.session_state.last_agent = None
    if "graph" not in st.session_state:
        st.session_state.graph = None


init_session_state()


# --- Sidebar ---
with st.sidebar:
    st.header("Configuration")

    # LLM Provider
    provider = st.selectbox(
        "LLM Provider",
        ["anthropic", "openai", "google"],
        index=["anthropic", "openai", "google"].index(
            os.getenv("LLM_PROVIDER", "anthropic")
        ),
    )

    # Model name
    default_models = {
        "anthropic": "claude-sonnet-4-5-20250929",
        "openai": "gpt-4o",
        "google": "gemini-2.5-flash",
    }
    model_name = st.text_input("Model Name", value=default_models.get(provider, ""))

    # Temperature
    temperature = st.slider("Temperature", 0.0, 1.0, 0.0, 0.1)

    st.divider()

    # PDF Upload
    st.header("Document Management")
    uploaded_files = st.file_uploader(
        "Upload Policy PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload company policy PDFs to add to the knowledge base.",
    )

    if uploaded_files:
        if st.button("Index Uploaded PDFs"):
            with st.spinner("Processing and indexing PDFs..."):
                try:
                    from src.db.vector_store import add_pdf_files

                    temp_paths = []
                    for uploaded_file in uploaded_files:
                        temp_path = os.path.join(
                            tempfile.gettempdir(), uploaded_file.name
                        )
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        temp_paths.append(temp_path)

                    num_chunks = add_pdf_files(temp_paths)
                    st.success(
                        f"Indexed {len(uploaded_files)} PDF(s) "
                        f"({num_chunks} chunks) into the knowledge base."
                    )

                    # Clean up temp files
                    for p in temp_paths:
                        if os.path.exists(p):
                            os.remove(p)
                except Exception as e:
                    st.error(f"Error indexing PDFs: {e}")

    st.divider()

    # System Info
    st.header("System Info")
    db_path = os.getenv("SQLITE_DB_PATH", "data/customer_support.db")
    if os.path.exists(db_path):
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers")
        num_customers = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tickets")
        num_tickets = cursor.fetchone()[0]
        conn.close()
        st.metric("Customers in DB", num_customers)
        st.metric("Support Tickets", num_tickets)
    else:
        st.warning("Database not found. Run `python scripts/setup.py` first.")

    chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "data/chroma")
    if os.path.exists(chroma_dir):
        st.metric("Vector Store", "Active")
    else:
        st.metric("Vector Store", "Not initialized")

    if st.session_state.last_agent:
        agent_labels = {
            "sql_agent": "SQL Agent (Database)",
            "rag_agent": "RAG Agent (Policies)",
            "general": "General Agent",
        }
        st.info(
            f"Last query handled by: **{agent_labels.get(st.session_state.last_agent, st.session_state.last_agent)}**"
        )

    st.divider()
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.last_agent = None
        st.session_state.graph = None
        st.rerun()


# --- Build Graph (cached per config) ---
@st.cache_resource
def get_graph(_provider, _model, _temperature):
    """Build and cache the agent graph based on LLM configuration."""
    from src.config.settings import get_llm
    from src.graph import build_graph

    llm = get_llm(provider=_provider, model=_model, temperature=_temperature)
    return build_graph(llm=llm)


# --- Main Chat Interface ---
st.title("AI Customer Support Assistant")
st.caption(
    "Ask about customer data, support tickets, company policies, or general questions."
)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("How can I help you today?"):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get or build graph
    with st.spinner("Thinking..."):
        try:
            graph = get_graph(provider, model_name, temperature)

            # Invoke the graph
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            result = graph.invoke(
                {
                    "messages": [{"role": "user", "content": prompt}],
                    "query_category": "",
                    "customer_id": "",
                },
                config=config,
            )

            # Extract the response
            agent_messages = result.get("messages", [])
            response = "I wasn't able to process your request. Please try again."

            if agent_messages:
                last_msg = agent_messages[-1]
                if hasattr(last_msg, "content"):
                    response = last_msg.content
                elif isinstance(last_msg, dict):
                    response = last_msg.get("content", response)

            # Track which agent handled the query
            st.session_state.last_agent = result.get("query_category", "unknown")

            # Display assistant response
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)

        except Exception as e:
            error_msg = f"Error: {e}"
            st.session_state.messages.append(
                {"role": "assistant", "content": error_msg}
            )
            with st.chat_message("assistant"):
                st.error(error_msg)
