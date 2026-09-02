import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_FILE = BASE_DIR / "assets" / "Keday70_Sales_Dataset_2024_v2.xlsx"
DB_FILE   = BASE_DIR / "keday70.db"

PAGE_TITLE = "Keday70 BI Dashboard"
PAGE_ICON = ""
LAYOUT = "wide"

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")

# Production Configs
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")

# ── Warna tema ────────────────────────────────────────────────────────────────
COLOR_PRIMARY  = "#4ECCA3"
COLOR_SECONDARY= "#00B8D9"
COLOR_ACCENT   = "#7F77DD"
COLOR_WARNING  = "#EF9F27"
COLOR_DANGER   = "#E24B4A"
COLOR_SUCCESS  = "#97C459"
COLOR_BG       = "#0F1117"
COLOR_SURFACE  = "#1A1F2E"
COLOR_SURFACE2 = "#212840"
COLOR_BORDER   = "rgba(255,255,255,0.07)"

CHART_COLORS = [
    COLOR_PRIMARY, COLOR_ACCENT, COLOR_WARNING,
    COLOR_SECONDARY, COLOR_SUCCESS, COLOR_DANGER,
    "#F09595", "#9FE1CB", "#FAC775",
]

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="rgba(255,255,255,0.65)",
    font_size=11,
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font_size=11,
        orientation="h",
        yanchor="bottom", y=1.02,
        xanchor="right", x=1,
    ),
    transition=dict(duration=0),
    uirevision=True,
)

# Config Plotly — dipakai di setiap st.plotly_chart(config=PLOTLY_CONFIG)
PLOTLY_CONFIG = dict(
    displayModeBar=False,
    staticPlot=False,
    responsive=True,
)
