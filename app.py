import os

import streamlit as st

from agent import run_agent
from guardrails import check as guardrail_check

st.set_page_config(
    page_title="Well Completion Design Advisor",
    page_icon="🛢️",
    layout="wide",
)

# ── API key guard ─────────────────────────────────────────────────────────────
if not os.environ.get("OPENAI_API_KEY"):
    st.error(
        "**OPENAI_API_KEY is not set.** "
        "Add it as an environment variable or as a Hugging Face Space secret named `OPENAI_API_KEY`."
    )
    st.stop()

# ── Session state initialisation ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []      # list of {"role": ..., "content": ...}
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False

# ── Sidebar — well parameters form ───────────────────────────────────────────
with st.sidebar:
    st.title("🛢️ Well Parameters")
    st.markdown("Configure the well below, then click **Analyze**.")

    formation_type = st.selectbox(
        "Formation Type",
        ["Sandstone", "Limestone", "Shale", "Tight Gas", "Carbonate"],
    )
    depth_ft = st.number_input(
        "Depth (ft TVD)", min_value=1_000, max_value=25_000, value=8_500, step=100
    )
    reservoir_pressure = st.number_input(
        "Reservoir Pressure (psi)", min_value=100, max_value=25_000, value=3_200, step=50
    )
    bht = st.number_input(
        "Bottom Hole Temperature (°F)", min_value=50, max_value=500, value=180, step=5
    )
    fluid_type = st.selectbox(
        "Completion / Drilling Fluid", ["Water-based", "Oil-based", "Gas"]
    )
    net_pay = st.number_input(
        "Net Pay (ft)", min_value=1.0, max_value=500.0, value=45.0, step=1.0
    )
    skin_factor = st.slider("Skin Factor", min_value=-5, max_value=20, value=5)

    st.divider()
    analyze_btn = st.button("Analyze", type="primary", use_container_width=True)

    if st.session_state.analyzed:
        if st.button("Reset Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.analyzed = False
            st.rerun()

# ── Main — chat area ──────────────────────────────────────────────────────────
st.title("Well Completion Design Advisor")

# Replay existing chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


def _run_and_display(input_messages: list[dict]) -> str:
    """Run the agent and stream tool-call badges + final response into the UI."""
    with st.chat_message("assistant"):
        badge_container = st.container()
        response_slot = st.empty()
        seen_tools: list[str] = []

        def on_tool_call(tool_name: str) -> None:
            seen_tools.append(tool_name)
            with badge_container:
                for tn in seen_tools:
                    with st.expander(f"🔧 `{tn}`", expanded=False):
                        st.caption(f"Executed tool: **{tn}**")

        with st.spinner("Thinking…"):
            reply = run_agent(input_messages, on_tool_call=on_tool_call)

        response_slot.markdown(reply)

    return reply


# ── Analyze button — inject well parameters and run agent ─────────────────────
if analyze_btn:
    user_msg = (
        f"Please analyse this well and produce a complete completion design recommendation.\n\n"
        f"**Well Parameters:**\n"
        f"- Formation Type: {formation_type}\n"
        f"- Depth (TVD): {depth_ft:,} ft\n"
        f"- Reservoir Pressure: {reservoir_pressure:,} psi\n"
        f"- Bottom Hole Temperature: {bht} °F\n"
        f"- Completion / Drilling Fluid: {fluid_type}\n"
        f"- Net Pay: {net_pay} ft\n"
        f"- Skin Factor: {skin_factor}\n\n"
        f"Use all three tools (fracture gradient, perforation strategy, stimulation design) "
        f"before writing the report."
    )

    st.session_state.messages.append({"role": "user", "content": user_msg})
    st.session_state.analyzed = True

    with st.chat_message("user"):
        st.markdown(user_msg)

    reply = _run_and_display(
        [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    )
    st.session_state.messages.append({"role": "assistant", "content": reply})

# ── No analysis yet — show onboarding hint ────────────────────────────────────
if not st.session_state.analyzed:
    st.info(
        "Configure the well parameters in the sidebar and click **Analyze** to generate "
        "a completion design report. You can ask follow-up questions after the initial analysis."
    )

# ── Follow-up chat input — always rendered once analysis exists ───────────────
# st.chat_input must be called on every rerun to remain visible.
if st.session_state.analyzed:
    if prompt := st.chat_input("Ask a follow-up question…"):
        # Guardrail check before the message reaches the agent
        allowed, rejection_reason = guardrail_check(prompt)

        with st.chat_message("user"):
            st.markdown(prompt)

        if not allowed:
            with st.chat_message("assistant"):
                st.warning(rejection_reason)
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})

            reply = _run_and_display(
                [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            )
            st.session_state.messages.append({"role": "assistant", "content": reply})
