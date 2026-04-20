"""
Clinical Documentation Assistant
BITS CCZG506 Assignment II

Three NLP sub-tasks:
1. Clinical Note Summarization (base Claude Haiku OR fine-tuned Nova Micro)
2. Medical Entity Extraction (Claude Haiku)
3. RAG-based Medical Q&A (Bedrock Knowledge Bases)
"""
import os
import json
import boto3
import streamlit as st
from botocore.config import Config

# ============================================================
# Configuration
# ============================================================
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
KB_ID = os.getenv("KB_ID", "")
CLAUDE_MODEL_ID = "anthropic.claude-haiku-4-5-20251001-v1:0"

# After fine-tuning + provisioning throughput, set this env var to the
# provisioned model ARN (arn:aws:bedrock:REGION:ACCOUNT:provisioned-model/xxx)
NOVA_FT_MODEL_ARN = os.getenv("NOVA_FT_MODEL_ARN", "")

bedrock_runtime = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION,
    config=Config(read_timeout=120, retries={"max_attempts": 3}),
)
bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime", region_name=AWS_REGION
)


def invoke_claude(prompt: str, system: str = "", max_tokens: int = 1024) -> str:
    """Call Claude via InvokeModel Messages API."""
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system

    response = bedrock_runtime.invoke_model(
        modelId=CLAUDE_MODEL_ID,
        body=json.dumps(body),
    )
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def invoke_nova(
    model_id: str, prompt: str, system: str = "", max_tokens: int = 512
) -> str:
    """Call Nova (base or fine-tuned) via the Converse API."""
    kwargs = {
        "modelId": model_id,
        "messages": [
            {"role": "user", "content": [{"text": prompt}]}
        ],
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": 0.3},
    }
    if system:
        kwargs["system"] = [{"text": system}]

    response = bedrock_runtime.converse(**kwargs)
    return response["output"]["message"]["content"][0]["text"]


# ============================================================
# Streamlit UI
# ============================================================
st.set_page_config(
    page_title="Clinical Documentation Assistant",
    page_icon="🏥",
    layout="wide",
)

st.title("🏥 Clinical Documentation Assistant")
st.caption(
    "AI-powered clinical note processing. Powered by Amazon Bedrock: "
    "Claude Haiku 4.5 (base reasoning), Nova Micro (fine-tuned summarization), "
    "and Bedrock Knowledge Bases (RAG)."
)

tab1, tab2, tab3 = st.tabs(
    ["📝 Summarization", "🔬 Entity Extraction", "💬 Medical Q&A (RAG)"]
)

sample_note = """Patient is a 67-year-old male with a past medical history significant for
hypertension, type 2 diabetes mellitus, and hyperlipidemia who presented to the emergency
department with a 3-day history of progressively worsening shortness of breath, productive
cough with yellow-green sputum, and subjective fevers. Vital signs on admission: BP 148/92,
HR 102, RR 24, SpO2 89% on room air, T 38.6C. Chest X-ray showed a right lower lobe
consolidation consistent with community-acquired pneumonia. Started on ceftriaxone 1g IV
daily and azithromycin 500mg PO daily. Patient improved over 4 days and was discharged
home with a 7-day course of oral antibiotics, follow-up with PCP in 1 week, and strict
return precautions for worsening symptoms."""

# ============================================================
# Tab 1: Summarization (with model comparison)
# ============================================================
with tab1:
    st.header("Clinical Note Summarization")
    st.write(
        "Compare a general-purpose LLM (Claude Haiku 4.5) vs a domain-fine-tuned "
        "model (Nova Micro trained on MTSamples)."
    )

    note = st.text_area("Clinical Note", value=sample_note, height=250)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🧠 Claude Haiku 4.5 (base)")
        if st.button("Summarize with Claude", key="claude_btn"):
            system_prompt = (
                "You are a clinical documentation assistant. Summarize the given "
                "clinical note in a structured format with sections: Chief Complaint, "
                "Key Findings, Treatment, Disposition. Be concise and medically accurate."
            )
            with st.spinner("Generating..."):
                try:
                    summary = invoke_claude(
                        prompt=f"Summarize this clinical note:\n\n{note}",
                        system=system_prompt,
                        max_tokens=400,
                    )
                    st.success("Done")
                    st.markdown(summary)
                except Exception as e:
                    st.error(f"Error: {e}")

    with col2:
        st.subheader("🎯 Nova Micro (fine-tuned)")
        if not NOVA_FT_MODEL_ARN:
            st.info(
                "Fine-tuned model not configured. Set `NOVA_FT_MODEL_ARN` "
                "env var after creating Provisioned Throughput."
            )
            st.caption("You can still click below to test the base Nova Micro model.")
            use_arn = "amazon.nova-micro-v1:0"
        else:
            use_arn = NOVA_FT_MODEL_ARN
            st.caption(f"Using: `{use_arn[:60]}...`")

        if st.button("Summarize with Nova", key="nova_btn"):
            system_prompt = (
                "You are a clinical documentation assistant. Given a clinical note, "
                "produce a concise single-line description that captures the key clinical content."
            )
            with st.spinner("Generating..."):
                try:
                    summary = invoke_nova(
                        model_id=use_arn,
                        prompt=f"Summarize this clinical note:\n\n{note}",
                        system=system_prompt,
                        max_tokens=300,
                    )
                    st.success("Done")
                    st.markdown(summary)
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.caption(
                        "If this failed and you set NOVA_FT_MODEL_ARN, check that "
                        "Provisioned Throughput is InService."
                    )

# ============================================================
# Tab 2: Entity Extraction
# ============================================================
with tab2:
    st.header("Medical Entity Extraction")
    st.write(
        "Extract structured clinical entities: medications, conditions, "
        "procedures, vital signs."
    )

    ner_note = st.text_area(
        "Clinical Text", value=sample_note, height=200, key="ner_input"
    )

    if st.button("Extract Entities", type="primary", key="ner_btn"):
        system_prompt = """You are a medical NLP system. Extract entities from the clinical text.
Return ONLY valid JSON with this exact structure, no preamble, no markdown fences:
{
  "medications": [{"name": "...", "dose": "...", "route": "...", "frequency": "..."}],
  "conditions": ["..."],
  "procedures": ["..."],
  "vital_signs": [{"measure": "...", "value": "..."}],
  "demographics": {"age": "...", "sex": "..."}
}"""
        with st.spinner("Extracting entities..."):
            try:
                response = invoke_claude(
                    prompt=f"Extract entities from this note:\n\n{ner_note}",
                    system=system_prompt,
                    max_tokens=1500,
                )
                clean = (
                    response.strip()
                    .removeprefix("```json")
                    .removeprefix("```")
                    .removesuffix("```")
                    .strip()
                )
                entities = json.loads(clean)

                col_a, col_b = st.columns(2)
                with col_a:
                    st.subheader("💊 Medications")
                    for med in entities.get("medications", []):
                        st.write(
                            f"**{med.get('name', '')}** - "
                            f"{med.get('dose', '')} "
                            f"{med.get('route', '')} "
                            f"{med.get('frequency', '')}"
                        )

                    st.subheader("🩺 Conditions")
                    for cond in entities.get("conditions", []):
                        st.write(f"• {cond}")

                with col_b:
                    st.subheader("📊 Vital Signs")
                    for vs in entities.get("vital_signs", []):
                        st.write(
                            f"**{vs.get('measure', '')}**: {vs.get('value', '')}"
                        )

                    st.subheader("🔧 Procedures")
                    for proc in entities.get("procedures", []):
                        st.write(f"• {proc}")

                    demo = entities.get("demographics", {})
                    if demo:
                        st.subheader("👤 Demographics")
                        st.write(
                            f"Age: {demo.get('age', 'N/A')} | "
                            f"Sex: {demo.get('sex', 'N/A')}"
                        )

                with st.expander("Raw JSON"):
                    st.json(entities)
            except json.JSONDecodeError as e:
                st.error(f"Failed to parse JSON: {e}")
                st.text(response)
            except Exception as e:
                st.error(f"Error: {e}")

# ============================================================
# Tab 3: RAG Medical Q&A
# ============================================================
with tab3:
    st.header("Medical Knowledge Q&A")
    st.write(
        "Ask medical questions grounded in indexed clinical guidelines "
        "(WHO, CDC, NIH) via Amazon Bedrock Knowledge Bases."
    )

    if not KB_ID:
        st.warning("`KB_ID` environment variable is not set. RAG will not work.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("citations"):
                with st.expander("📚 Sources"):
                    for i, cit in enumerate(msg["citations"], 1):
                        st.write(f"**Source {i}:** {cit}")

    if query := st.chat_input("Ask a medical question..."):
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                try:
                    response = bedrock_agent_runtime.retrieve_and_generate(
                        input={"text": query},
                        retrieveAndGenerateConfiguration={
                            "type": "KNOWLEDGE_BASE",
                            "knowledgeBaseConfiguration": {
                                "knowledgeBaseId": KB_ID,
                                "modelArn": f"arn:aws:bedrock:{AWS_REGION}::foundation-model/{CLAUDE_MODEL_ID}",
                            },
                        },
                    )
                    answer = response["output"]["text"]
                    st.markdown(answer)

                    citations = []
                    for cit in response.get("citations", []):
                        for ref in cit.get("retrievedReferences", []):
                            src = ref.get("location", {}).get("s3Location", {}).get(
                                "uri", "Unknown"
                            )
                            citations.append(src)

                    unique_cits = list(set(citations))
                    if unique_cits:
                        with st.expander("📚 Sources"):
                            for i, cit in enumerate(unique_cits, 1):
                                st.write(f"**Source {i}:** {cit}")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "citations": unique_cits,
                    })
                except Exception as e:
                    st.error(f"Error: {e}")

# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.header("About")
    st.write(
        "**Domain:** Healthcare  \n"
        "**Category:** Natural Language Processing  \n"
        "**Sub-tasks:**  \n"
        "1. Text Summarization  \n"
        "2. Named Entity Recognition  \n"
        "3. Question Answering (RAG)  "
    )
    st.divider()
    st.subheader("Tech Stack")
    st.write(
        "- Amazon Bedrock\n"
        "- Claude Haiku 4.5 (reasoning)\n"
        "- Nova Micro (fine-tuned)\n"
        "- Titan Embeddings V2\n"
        "- Bedrock Knowledge Bases\n"
        "- OpenSearch Serverless\n"
        "- Streamlit on EC2\n"
        "- Terraform IaC"
    )
    st.divider()
    st.caption(f"KB: {KB_ID[:15]}..." if KB_ID else "KB: not set")
    st.caption(
        f"FT Nova: configured" if NOVA_FT_MODEL_ARN else "FT Nova: not set (base model used)"
    )
    st.caption(f"Region: {AWS_REGION}")
