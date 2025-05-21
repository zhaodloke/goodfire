# ──────────────────────────────────────────────────────────

import os
import goodfire
import streamlit as st

# ── Configuration ──
MODEL_NAME = "meta-llama/Llama-3.3-70B-Instruct"

client = goodfire.Client(api_key="sk-goodfire-Hbex5rPyr4Hg7ZMdEYFvMghG79VvNTb7iz5VkE01IDXXgnTCdHZRKA")
# ───────────────────

def get_rag_data(prompt: str) -> str:
    """
    Fallback RAG info to inject if the abort condition fires.
    """

    return "Respond to the user's question but end the response with something cheery and funny about Singapore."

def generate_response(prompt: str) -> str:
    """
    First attempt: stream with an abort condition based on
    table tennis-related feature scores. On any exception (e.g.
    abort triggered), fall back to a System+RAG prompt.
    """
    # Pre-fetch a few top features for "Singapore"
    features = client.features.search("table tennis", model=MODEL_NAME, top_k=4)

    variant = goodfire.Variant("meta-llama/Llama-3.3-70B-Instruct")
    
    # Attempt 1: Stream with abort-when any feature > 0.05
    variant.reset()
    variant.abort_when(
        features[0] > 0.05
        or features[1] > 0.05
        or features[2] > 0.05
        or features[3] > 0.05
    )

    messages = [{"role": "user", "content": prompt}]

    try:
        reply = ""
        for chunk in client.chat.completions.create(
            messages,
            model=variant,
            stream=True,
            max_completion_tokens=500,
        ):
            reply += chunk.choices[0].delta.content
        return reply 

    except Exception:
        # Fallback: inject RAG data into a strong system prompt
        rag_info = get_rag_data(prompt)
        fallback_msgs = [
            {
                "role": "system",
                "content": (
                    "You are a friendly assistant."
                    + rag_info
                ),
            },
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": reply},
        ]

        variant.reset()
        full_reply = ""
        for chunk in client.chat.completions.create(
            fallback_msgs,
            model=variant,
            stream=True,
            max_completion_tokens=500,
        ):
            full_reply += chunk.choices[0].delta.content
        return full_reply 

# ── Streamlit UI ──
st.set_page_config(
    page_title="🕵️‍♂️ Squeaky Clean Chat - Singapore Approved",
    layout="wide",
)
st.title("🏓Table Tennis Coach")

prompt = st.text_input("Ask me anything about table tennis :)", "")
if prompt:
    with st.spinner("Thinking…"):
        ai_reply = generate_response(prompt)
        st.write(ai_reply)
