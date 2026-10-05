# Cisco AI Assistant

> AI-powered network diagram generator — describe your network in plain English, get validated topology diagrams.

---

## Global Architecture

```mermaid
flowchart TD
    A["👤 User"] -->|"Natural language prompt"| B["🐍 Python CLI\n(simple input)"]
    B -->|"Raw text"| C["🤖 LLM\n(Gemini / OpenAI)"]
    C -->|"Structured JSON"| D["📋 Pydantic Model\n(Schema validation)"]
    D -->|"Validated data"| E["🔍 Network Validator\n(Logical checks)"]
    E -->|"Clean topology"| F["🎨 Diagram Generator\n(Graphviz)"]
    F -->|"Render"| G["🖼️ PNG / SVG Output"]

    style A fill:#4FC3F7,stroke:#0288D1,color:#000
    style B fill:#81C784,stroke:#388E3C,color:#000
    style C fill:#FFB74D,stroke:#F57C00,color:#000
    style D fill:#CE93D8,stroke:#7B1FA2,color:#000
    style E fill:#EF5350,stroke:#C62828,color:#fff
    style F fill:#FFD54F,stroke:#F9A825,color:#000
    style G fill:#A5D6A7,stroke:#2E7D32,color:#000
```

---

## Workflow

```mermaid
flowchart LR
    P["Prompt"] --> L["LLM"]
    L --> J["Network JSON"]
    J --> V["Pydantic\nValidation"]
    V --> GR["Graph\nRepresentation"]
    GR --> R["Renderer"]
    R --> D["Diagram"]

    style P fill:#4FC3F7,stroke:#0288D1,color:#000
    style L fill:#FFB74D,stroke:#F57C00,color:#000
    style J fill:#CE93D8,stroke:#7B1FA2,color:#000
    style V fill:#EF5350,stroke:#C62828,color:#fff
    style GR fill:#FFD54F,stroke:#F9A825,color:#000
    style R fill:#81C784,stroke:#388E3C,color:#000
    style D fill:#A5D6A7,stroke:#2E7D32,color:#000
```

---

## Component Details

| Component             | Role                                                        |
| --------------------- | ----------------------------------------------------------- |
| **Python CLI**        | Accepts natural-language descriptions from the user         |
| **LLM**              | Parses the prompt and produces a structured network JSON    |
| **Pydantic Model**   | Validates the JSON against a strict schema                  |
| **Network Validator** | Runs logical checks (duplicate IPs, orphan nodes, loops…)   |
| **Diagram Generator** | Converts the validated topology into a visual graph         |
| **Output**            | Renders the final diagram as PNG or SVG via Graphviz        |

---

## Getting Started

```bash
# Clone the repository
git clone https://github.com/<your-org>/cisco-ai-assistant.git
cd cisco-ai-assistant

# Install dependencies
pip install -r requirements.txt

# Run the assistant
python main.py
```

---

## Tech Stack

```mermaid
flowchart LR
    subgraph Frontend
        CLI["Python CLI"]
    end
    subgraph AI
        LLM["Gemini / OpenAI"]
    end
    subgraph Validation
        PY["Pydantic"]
        NV["Network Validator"]
    end
    subgraph Rendering
        GV["Graphviz"]
    end

    CLI --> LLM --> PY --> NV --> GV
```

---

## License

MIT       
