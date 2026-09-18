import random
import streamlit as st

st.set_page_config(page_title="Polyatomic Ion Quiz", layout="centered")

# ---------------------------------------------------------------------------
# Data: (formula, name, charge) exactly as given on the reference sheet.
# Formula strings use "_" before digits to mark subscripts, e.g. "NH_4".
# ---------------------------------------------------------------------------
IONS = [
    ("NH_4", "ammonium", "+1"),
    ("H_3O", "hydronium", "+1"),
    ("CN", "cyanide", "-1"),
    ("OH", "hydroxide", "-1"),
    ("ClO", "hypochlorite", "-1"),
    ("ClO_2", "chlorite", "-1"),
    ("ClO_3", "chlorate", "-1"),
    ("ClO_4", "perchlorate", "-1"),
    ("C_2H_3O_2", "acetate", "-1"),
    ("MnO_4", "permanganate", "-1"),
    ("NO_2", "nitrite", "-1"),
    ("NO_3", "nitrate", "-1"),
    ("HCO_3", "hydrogen carbonate (bicarbonate)", "-1"),
    ("CO_3", "carbonate", "-2"),
    ("CrO_4", "chromate", "-2"),
    ("Cr_2O_7", "dichromate", "-2"),
    ("O_2", "peroxide", "-2"),
    ("SO_3", "sulfite", "-2"),
    ("SO_4", "sulfate", "-2"),
    ("C_2O_4", "oxalate", "-2"),
    ("PO_4", "phosphate", "-3"),
    ("PO_3", "phosphite", "-3"),
]


def format_formula(raw: str) -> str:
    """Turn 'ClO_4' into 'ClO₄' style display using unicode subscripts."""
    sub_map = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    parts = raw.split("_")
    out = parts[0]
    for chunk in parts[1:]:
        # chunk may start with digits (the subscript) then continue with letters
        digits = ""
        rest = ""
        i = 0
        while i < len(chunk) and chunk[i].isdigit():
            digits += chunk[i]
            i += 1
        rest = chunk[i:]
        out += digits.translate(sub_map) + rest
    return out


def normalize_formula(text: str) -> str:
    """Normalize a user-typed formula for comparison: strip spaces, case-fold
    element casing carefully (chemistry is case-sensitive for elements, but we
    allow the user to skip subscript underscores/carets), and drop punctuation
    like ^, _, -, (charges) that isn't part of the ion itself."""
    if not text:
        return ""
    t = text.strip()
    # remove common charge annotations the student might accidentally include
    for junk in ["^", "-1", "-2", "-3", "+1", "(aq)", " "]:
        t = t.replace(junk, "")
    t = t.replace("_", "")
    return t


def normalize_name(text: str) -> str:
    if not text:
        return ""
    t = text.strip().lower()
    t = t.replace("-", " ")
    t = " ".join(t.split())
    return t


def normalize_charge(text: str) -> str:
    if not text:
        return ""
    t = text.strip().replace(" ", "")
    t = t.replace("−", "-")  # unicode minus -> hyphen
    if not t.startswith("+") and not t.startswith("-"):
        t = "+" + t
    return t


def check_formula(user_text: str, correct_raw: str) -> bool:
    user_norm = normalize_formula(user_text).lower()
    correct_norm = normalize_formula(correct_raw).lower()
    return user_norm == correct_norm


def check_name(user_text: str, correct_name: str) -> bool:
    user_norm = normalize_name(user_text)
    correct_norm = normalize_name(correct_name)
    # accept the bicarbonate alternate name specifically
    if correct_norm.startswith("hydrogen carbonate"):
        return user_norm in ("hydrogen carbonate", "bicarbonate")
    return user_norm == correct_norm


def check_charge(user_text: str, correct_charge: str) -> bool:
    return normalize_charge(user_text) == normalize_charge(correct_charge)


# ---------------------------------------------------------------------------
# Session state setup
# ---------------------------------------------------------------------------
if "quiz" not in st.session_state:
    st.session_state.quiz = None  # list of dicts: {formula, name, charge, given, answers...}
if "submitted" not in st.session_state:
    st.session_state.submitted = False


def start_quiz(num_questions: int):
    chosen = random.sample(IONS, num_questions) if num_questions < len(IONS) else list(IONS)
    random.shuffle(chosen)
    quiz = []
    for formula, name, charge in chosen:
        given = random.choice(["formula", "name"])
        quiz.append(
            {
                "formula": formula,
                "name": name,
                "charge": charge,
                "given": given,
            }
        )
    st.session_state.quiz = quiz
    st.session_state.submitted = False


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("⚗️ Polyatomic Ion Quiz")
st.caption(
    "You'll be given either the formula or the name for each ion. "
    "Fill in the blank plus the charge — every answer is typed, no multiple choice."
)

with st.sidebar:
    st.header("New Test")
    mode = st.radio("Test size", ["All ions", "Custom number"])
    if mode == "All ions":
        n = len(IONS)
    else:
        n = st.slider("How many ions?", min_value=1, max_value=len(IONS), value=5)

    if st.button("🎲 Generate Test", use_container_width=True, type="primary"):
        start_quiz(n)

    st.divider()
    st.caption(f"There are {len(IONS)} ions total in the reference table.")

if st.session_state.quiz is None:
    st.info("⬅️ Pick a test size in the sidebar and click **Generate Test** to begin.")
else:
    quiz = st.session_state.quiz

    with st.form("quiz_form"):
        st.write(f"### Fill in the table ({len(quiz)} ions)")

        header = st.columns([2.2, 2.6, 1.2])
        header[0].markdown("**Formula**")
        header[1].markdown("**Name**")
        header[2].markdown("**Charge**")

        for i, item in enumerate(quiz):
            c1, c2, c3 = st.columns([2.2, 2.6, 1.2])
            if item["given"] == "formula":
                c1.markdown(f"<div style='padding-top:8px'>{format_formula(item['formula'])}</div>", unsafe_allow_html=True)
                c2.text_input("Name", key=f"name_{i}", label_visibility="collapsed", placeholder="type name")
            else:
                c1.text_input("Formula", key=f"formula_{i}", label_visibility="collapsed", placeholder="e.g. ClO_3")
                c2.markdown(f"<div style='padding-top:8px'>{item['name']}</div>", unsafe_allow_html=True)
            c3.text_input("Charge", key=f"charge_{i}", label_visibility="collapsed", placeholder="+1 / -2")

        submitted = st.form_submit_button("✅ Grade my answers", type="primary", use_container_width=True)
        if submitted:
            st.session_state.submitted = True

    if st.session_state.submitted:
        st.write("---")
        st.write("## Results")

        correct_count = 0
        total_count = 0

        for i, item in enumerate(quiz):
            row_ok = True
            details = []

            if item["given"] == "formula":
                user_name = st.session_state.get(f"name_{i}", "")
                ok = check_name(user_name, item["name"])
                total_count += 1
                if ok:
                    correct_count += 1
                else:
                    row_ok = False
                details.append(("Name", user_name, item["name"], ok))
            else:
                user_formula = st.session_state.get(f"formula_{i}", "")
                ok = check_formula(user_formula, item["formula"])
                total_count += 1
                if ok:
                    correct_count += 1
                else:
                    row_ok = False
                details.append(("Formula", user_formula, format_formula(item["formula"]), ok))

            user_charge = st.session_state.get(f"charge_{i}", "")
            ok_charge = check_charge(user_charge, item["charge"])
            total_count += 1
            if ok_charge:
                correct_count += 1
            else:
                row_ok = False
            details.append(("Charge", user_charge, item["charge"], ok_charge))

            icon = "✅" if row_ok else "❌"
            label = f"{format_formula(item['formula'])} — {item['name']}"
            with st.expander(f"{icon} {label}", expanded=not row_ok):
                for field, user_val, correct_val, ok in details:
                    if ok:
                        st.write(f"**{field}:** {user_val or '(blank)'} ✅")
                    else:
                        st.write(f"**{field}:** {user_val or '(blank)'} ❌  → correct answer: **{correct_val}**")

        st.write("---")
        pct = round(100 * correct_count / total_count) if total_count else 0
        st.metric("Score", f"{correct_count} / {total_count}", f"{pct}%")

        if st.button("🔁 New test with same settings"):
            start_quiz(len(quiz))
            st.rerun()
