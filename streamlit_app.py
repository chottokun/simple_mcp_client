import streamlit as st
import requests

# --- Page Configuration ---
st.set_page_config(page_title="Intelligent RAG Chat", page_icon="🤖", layout="wide")

st.title("🤖 Intelligent RAG Chat System")
st.caption("Ask me anything about our company's documents!")

# --- API Configuration ---
API_BASE_URL = "http://backend:8000"
CHAT_API_URL = f"{API_BASE_URL}/api/chat"

# --- Session State Initialization ---
# 'messages' will store the history of the conversation
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- UI Rendering ---
# Display the chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # If the message is from the assistant and has sources, display them
        if (
            message["role"] == "assistant"
            and "sources" in message
            and message["sources"]
        ):
            with st.expander("View Sources"):
                for source in message["sources"]:
                    st.info(
                        f"**Source:** {source['document_name']}\n\n**Snippet:** {source['snippet']}"
                    )


# --- User Input Handling ---
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response while processing
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")

        try:
            # Prepare request payload
            payload = {
                "message": prompt,
                "session_id": "static_session_id",  # Using a static session ID for now
            }

            # Call the backend API
            response = requests.post(CHAT_API_URL, json=payload)
            response.raise_for_status()

            response_data = response.json()
            answer = response_data.get("answer", "Sorry, I couldn't find an answer.")
            sources = response_data.get("sources", [])

            # Display the final answer
            message_placeholder.markdown(answer)

            # Add the full assistant message to history (including sources)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "sources": sources}
            )

            # Display sources in an expander
            if sources:
                with st.expander("View Sources"):
                    for source in sources:
                        st.info(
                            f"**Source:** {source['document_name']}\n\n**Snippet:** {source['snippet']}"
                        )

        except requests.exceptions.RequestException as e:
            error_message = f"Could not connect to the backend: {e}"
            message_placeholder.error(error_message)
            st.session_state.messages.append(
                {"role": "assistant", "content": error_message}
            )
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            message_placeholder.error(error_message)
            st.session_state.messages.append(
                {"role": "assistant", "content": error_message}
            )
