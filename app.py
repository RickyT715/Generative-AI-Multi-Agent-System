"""Streamlit UI for the AI Customer Support Assistant."""

import os
import uuid

import streamlit as st
from dotenv import load_dotenv, set_key

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

    # Known models per provider
    PROVIDER_MODELS = {
        "anthropic": ["claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001"],
        "openai": ["gpt-4o", "gpt-4o-mini", "o3-mini"],
        "google": ["gemini-2.5-flash", "gemini-2.5-pro"],
    }
    PROVIDERS = list(PROVIDER_MODELS.keys())

    # Load persisted values from .env as defaults
    env_provider = os.getenv("LLM_PROVIDER", "anthropic")
    env_model = os.getenv("LLM_MODEL", "")
    try:
        env_temperature = float(os.getenv("LLM_TEMPERATURE", "0.0"))
    except ValueError:
        env_temperature = 0.0

    # Provider selector
    provider = st.selectbox(
        "LLM Provider",
        PROVIDERS,
        index=PROVIDERS.index(env_provider) if env_provider in PROVIDERS else 0,
    )

    # Model selector with Custom option
    models = PROVIDER_MODELS[provider]
    model_options = models + ["Custom..."]

    if env_model in models:
        default_model_index = models.index(env_model)
    elif env_model and provider == env_provider:
        default_model_index = len(models)  # "Custom..."
    else:
        default_model_index = 0

    selected_model = st.selectbox(
        "Model",
        model_options,
        index=default_model_index,
        key=f"model_select_{provider}",
    )

    if selected_model == "Custom...":
        model_name = st.text_input(
            "Custom Model Name",
            value=env_model
            if (env_model not in models and provider == env_provider)
            else "",
        )
    else:
        model_name = selected_model

    # Temperature
    temperature = st.slider("Temperature", 0.0, 1.0, env_temperature, 0.1)

    # API Key inputs — use text type with CSS masking to prevent Chrome autofill.
    # Using type="password" causes Chrome to offer "Use a strong password", so we
    # use a regular text input and mask characters with CSS -webkit-text-security.
    st.markdown(
        """<style>
        div[data-testid="stExpander"] div[data-testid="stTextInputRootElement"] input {
            -webkit-text-security: disc;
            text-security: disc;
        }
        </style>""",
        unsafe_allow_html=True,
    )

    API_KEY_VARS = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
    }

    api_key_inputs = {}
    with st.expander("API Keys", expanded=False):
        for prov, env_var in API_KEY_VARS.items():
            existing = os.getenv(env_var, "")
            if existing:
                masked = existing[:6] + "..." + existing[-4:]
            else:
                masked = ""

            label = f"{prov.title()} API Key"
            if prov == provider and existing:
                label += " \u2705"

            api_key_inputs[env_var] = st.text_input(
                label,
                value="",
                placeholder=masked or "Enter API key",
                key=f"api_key_{prov}",
            )

    # Save Settings button
    if st.button("Save Settings", type="primary"):
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        set_key(env_path, "LLM_PROVIDER", provider)
        set_key(env_path, "LLM_MODEL", model_name)
        set_key(env_path, "LLM_TEMPERATURE", str(temperature))

        for env_var, new_key in api_key_inputs.items():
            if new_key.strip():
                set_key(env_path, env_var, new_key.strip())

        load_dotenv(override=True)
        st.cache_resource.clear()
        st.success("Settings saved!")

    st.divider()

    # File Upload
    st.header("Document Management")
    uploaded_files = st.file_uploader(
        "Upload Files",
        type=["csv", "pdf", "txt"],
        accept_multiple_files=True,
        help="CSV files go to SQL database. PDF/TXT files go to the vector store.",
    )

    if uploaded_files:
        if st.button("Process Uploaded Files"):
            try:
                from src.processing.file_processor import process_uploaded_files

                success, failure = process_uploaded_files(uploaded_files, st)
                if success:
                    st.success(f"Processed {success} file(s) successfully.")
                if failure:
                    st.warning(f"{failure} file(s) had errors.")
            except Exception as e:
                st.error(f"Error processing files: {e}")

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
        cursor.execute("SELECT COUNT(*) FROM products")
        num_products = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tickets")
        num_tickets = cursor.fetchone()[0]
        conn.close()
        st.metric("Customers in DB", num_customers)
        st.metric("Products in DB", num_products)
        st.metric("Support Tickets", num_tickets)
    else:
        st.warning("Database not found. Run `python scripts/setup.py` first.")

    chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "data/chroma")
    if os.path.exists(chroma_dir):
        try:
            from src.db.vector_store import get_document_count

            doc_count = get_document_count()
            st.metric("Vector Store Docs", doc_count)
        except Exception:
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
