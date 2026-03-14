import streamlit as st

from utils.ux import sidebar, get_gateway_urls

sidebar()
st.title("Share your chatbot")
urls = get_gateway_urls()

st.subheader("Gateway Endpoints")

st.code(
    f"Health: {urls['http']}/health\nInfo: {urls['http']}/info\nWebSocket: {urls['ws']}/ws/{{session_id}}"
)

st.subheader("Embeddable iframe (custom client)")
st.write(
    "Use your own web client that connects to the websocket gateway."
)

st.code(
    """
<iframe src="/path-to-your-chat-ui"
width="100%"
height="700"
frameborder="0"
></iframe>
"""
)
st.subheader("Browser WebSocket Example")

st.write(
    "Connect directly from browser JavaScript to your gateway."
)
st.code(
    f"const ws = new WebSocket('{urls['ws']}/ws/' + crypto.randomUUID());"
)

st.info("Telegram connect from this UI is not wired yet in the websocket architecture.")
