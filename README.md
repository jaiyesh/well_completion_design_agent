---
title: Well Completion Design Advisor
emoji: 🛢️
colorFrom: red
colorTo: gray
sdk: streamlit
sdk_version: 1.36.0
app_file: app.py
pinned: false
---

# Well Completion Design Advisor

A Streamlit app where a petroleum engineer inputs well parameters and a GPT-4o tool-calling agent produces a full completion design recommendation via interactive chat.

## Features

- **Fracture gradient calculation** via Eaton's method
- **Perforation programme** recommendation based on formation type, net pay, and skin factor
- **Stimulation design** (hydraulic fracture or acid treatment) with fluid volume, proppant, pump rate, and expected geometry
- Interactive follow-up chat after the initial analysis
- Tool-call badges shown in real time while the agent is thinking

---

## Local development

### 1. Clone and install

```bash
git clone <your-repo-url>
cd completion_design
pip install -r requirements.txt
```

### 2. Set your OpenAI API key

```bash
export OPENAI_API_KEY="sk-..."
```

### 3. Run the app

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### 4. Test case (matches CLAUDE.md spec)

Set these values in the sidebar and click **Analyze**:

| Parameter | Value |
|---|---|
| Formation Type | Sandstone |
| Depth (ft) | 8500 |
| Reservoir Pressure (psi) | 3200 |
| Bottom Hole Temperature (°F) | 180 |
| Fluid Type | Water-based |
| Net Pay (ft) | 45 |
| Skin Factor | 5 |

Expected agent behaviour: calls all three tools, then returns a structured completion report.

---

## Deploy to Hugging Face Spaces

### Step 1 — Create a new Space

1. Log in at [huggingface.co](https://huggingface.co).
2. Click your profile icon → **New Space**.
3. Fill in:
   - **Space name**: e.g. `completion-design-advisor`
   - **License**: MIT (or your preference)
   - **SDK**: select **Streamlit**
   - **Python version**: 3.11
4. Click **Create Space**.

### Step 2 — Add your OpenAI API key as a secret

> Secrets are encrypted environment variables — never commit your key to the repo.

1. In your Space, go to **Settings → Variables and secrets**.
2. Click **New secret**.
3. Set:
   - **Name**: `OPENAI_API_KEY`
   - **Value**: your OpenAI key (`sk-...`)
4. Click **Save**.

The app reads it with `os.environ["OPENAI_API_KEY"]` at runtime.

### Step 3 — Push your code

Option A — via the HF web UI (drag and drop files):

Upload `app.py`, `agent.py`, `tools.py`, `prompts.py`, and `requirements.txt` through the **Files** tab.

Option B — via Git:

```bash
# Install the HF CLI if needed
pip install huggingface_hub

# Log in
huggingface-cli login

# Add the Space as a remote (replace USERNAME and SPACE_NAME)
git remote add hf https://huggingface.co/spaces/USERNAME/SPACE_NAME

# Push
git push hf main
```

### Step 4 — Verify the deployment

1. Open the Space URL (shown at the top of the Space page).
2. Wait for the build to finish (watch the **Logs** tab).
3. Enter the test case values above and click **Analyze**.
4. Confirm the agent calls all three tools and returns a full report.

### Troubleshooting

| Symptom | Fix |
|---|---|
| `OPENAI_API_KEY is not set` banner | Check Settings → Secrets; key name must be exact |
| Build fails at `pip install` | Verify `requirements.txt` is in the repo root |
| `ModuleNotFoundError` | Make sure all `.py` files were pushed |
| Blank response from agent | Check Space logs for OpenAI API errors (quota, wrong key) |

---

## File structure

```
completion_design/
├── app.py            # Streamlit UI — sidebar form, chat history, calls agent.py
├── agent.py          # OpenAI tool-calling agent loop
├── tools.py          # Three tool functions + TOOL_SCHEMAS for the OpenAI API
├── prompts.py        # SYSTEM_PROMPT
├── requirements.txt  # Pinned Python dependencies
└── README.md         # This file
```
