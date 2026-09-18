import random
import streamlit as st

st.set_page_config(page_title="Polyatomic Ion Quiz", layout="centered")

# ---------------------------------------------------------------------------
# Data: (formula, name, charge) exactly as given on the reference sheet.
# Formula strings use "_" before digits to mark subscripts, e.g. "NH_4".
# ---------------------------------------------------------------------------
IONS = [
    ("NH_4", "ammonium", "+1"),
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
if "flash_order" not in st.session_state:
    st.session_state.flash_order = list(range(len(IONS)))
    random.shuffle(st.session_state.flash_order)
if "flash_pos" not in st.session_state:
    st.session_state.flash_pos = 0
if "flash_flipped" not in st.session_state:
    st.session_state.flash_flipped = False
if "flash_direction" not in st.session_state:
    st.session_state.flash_direction = "formula_front"  # "formula_front", "name_front", or "mixed"
if "flash_card_sides" not in st.session_state:
    st.session_state.flash_card_sides = {}  # idx -> "formula_front"/"name_front", set when mixed mode deals a card
if "known" not in st.session_state:
    st.session_state.known = set()      # indices into IONS the user marked "I know this"
if "learning" not in st.session_state:
    st.session_state.learning = set()   # indices into IONS the user marked "still learning"


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


def shuffle_flashcards(pool_indices=None):
    pool = pool_indices if pool_indices is not None else list(range(len(IONS)))
    random.shuffle(pool)
    st.session_state.flash_order = pool
    st.session_state.flash_pos = 0
    st.session_state.flash_flipped = False
    if st.session_state.flash_direction == "mixed":
        st.session_state.flash_card_sides = {
            i: random.choice(["formula_front", "name_front"]) for i in pool
        }
    else:
        st.session_state.flash_card_sides = {}


def side_for_card(idx: int) -> str:
    """Which side is shown first for this card, respecting the current mode."""
    if st.session_state.flash_direction == "mixed":
        # deal one lazily if this card hasn't been assigned a side yet
        if idx not in st.session_state.flash_card_sides:
            st.session_state.flash_card_sides[idx] = random.choice(["formula_front", "name_front"])
        return st.session_state.flash_card_sides[idx]
    return st.session_state.flash_direction


def next_card(step=1):
    st.session_state.flash_pos = (st.session_state.flash_pos + step) % len(st.session_state.flash_order)
    st.session_state.flash_flipped = False


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("⚗️ Polyatomic Ion Quiz")

page = st.radio("What do you want to do?", ["📝 Take a Test", "🧠 Study Mode"], horizontal=True)
st.write("")

if page == "🧠 Study Mode":
    st.caption(
        "Flip through flashcards to drill formula, name, and charge together. "
        "Mark cards as known or still-learning to build a focused deck."
    )

    tab_cards, tab_table = st.tabs(["🔄 Flashcards", "📊 Grouped Cheat Sheet"])

    # ---------------- Flashcards ----------------
    with tab_cards:
        direction_label = st.radio(
            "What should the front of the card show?",
            [
                "Show formula → recall name + charge",
                "Show name → recall formula + charge",
                "Mixed → randomly formula or name each card",
            ],
            horizontal=False,
        )
        new_direction = (
            "formula_front" if direction_label.startswith("Show formula")
            else "name_front" if direction_label.startswith("Show name")
            else "mixed"
        )
        if new_direction != st.session_state.flash_direction:
            st.session_state.flash_direction = new_direction
            # re-deal sides for the current deck so mixed mode kicks in right away
            if new_direction == "mixed":
                st.session_state.flash_card_sides = {
                    i: random.choice(["formula_front", "name_front"]) for i in st.session_state.flash_order
                }
            st.session_state.flash_flipped = False

        colA, colB, colC = st.columns(3)
        if colA.button("🔀 Shuffle all", use_container_width=True):
            shuffle_flashcards()
            st.rerun()
        if colB.button("🎯 Drill 'still learning' only", use_container_width=True):
            if st.session_state.learning:
                shuffle_flashcards(list(st.session_state.learning))
                st.rerun()
            else:
                st.warning("You haven't marked any cards as 'still learning' yet.")
        if colC.button("♻️ Reset known/learning marks", use_container_width=True):
            st.session_state.known = set()
            st.session_state.learning = set()
            st.rerun()

        st.progress(
            len(st.session_state.known) / len(IONS),
            text=f"Known: {len(st.session_state.known)} / {len(IONS)}   |   Still learning: {len(st.session_state.learning)}",
        )

        idx = st.session_state.flash_order[st.session_state.flash_pos]
        formula, name, charge = IONS[idx]
        card_num = st.session_state.flash_pos + 1
        card_total = len(st.session_state.flash_order)

        st.write(f"Card {card_num} / {card_total}")

        # The card itself
        card_style = (
            "border:2px solid #4A90D9; border-radius:16px; padding:40px 20px; "
            "text-align:center; font-size:28px; min-height:140px; "
            "display:flex; align-items:center; justify-content:center; "
            "background-color:rgba(74,144,217,0.07);"
        )
        if not st.session_state.flash_flipped:
            if side_for_card(idx) == "formula_front":
                front_text = format_formula(formula)
                prompt = "Tap **Flip** to see the name and charge."
            else:
                front_text = name
                prompt = "Tap **Flip** to see the formula and charge."
            front_html = f"<div style='{card_style}'>{front_text}</div>"
            st.markdown(front_html, unsafe_allow_html=True)
            st.caption(prompt)
        else:
            if side_for_card(idx) == "formula_front":
                back_main = name
            else:
                back_main = format_formula(formula)
            back_html = (
                f"<div style='{card_style}'>"
                f"{back_main}<br><span style='font-size:20px; opacity:0.75;'>charge: {charge}</span>"
                f"</div>"
            )
            st.markdown(back_html, unsafe_allow_html=True)

        st.write("")
        b1, b2, b3, b4 = st.columns(4)
        if b1.button("⬅️ Prev", use_container_width=True):
            next_card(-1)
            st.rerun()
        if b2.button("🔁 Flip", use_container_width=True, type="primary"):
            st.session_state.flash_flipped = not st.session_state.flash_flipped
            st.rerun()
        if b3.button("Next ➡️", use_container_width=True):
            next_card(1)
            st.rerun()
        if b4.button("Restart deck", use_container_width=True):
            shuffle_flashcards()
            st.rerun()

        st.write("")
        m1, m2 = st.columns(2)
        if m1.button("✅ I know this one", use_container_width=True):
            st.session_state.known.add(idx)
            st.session_state.learning.discard(idx)
            next_card(1)
            st.rerun()
        if m2.button("🔄 Still learning", use_container_width=True):
            st.session_state.learning.add(idx)
            st.session_state.known.discard(idx)
            next_card(1)
            st.rerun()

    # ---------------- Grouped cheat sheet ----------------
    with tab_table:
        st.write(
            "Ions naturally cluster by charge — memorizing them in these groups "
            "is usually faster than memorizing the whole list in order."
        )
        groups = {}
        for formula, name, charge in IONS:
            groups.setdefault(charge, []).append((formula, name))

        for charge in ["+1", "-1", "-2", "-3"]:
            if charge not in groups:
                continue
            st.markdown(f"#### Charge: {charge}")
            rows = groups[charge]
            cols = st.columns(2)
            half = (len(rows) + 1) // 2
            for col, chunk in zip(cols, [rows[:half], rows[half:]]):
                with col:
                    for formula, name in chunk:
                        st.write(f"**{format_formula(formula)}** — {name}")
            st.write("")

        st.info(
            "💡 Memory tip: the **-1** group is by far the biggest (mostly the "
            "'-ate/-ite/-ide' halogen and nitrogen/chlorine oxyanions) — learn that "
            "cluster first, then the small +1, -2, and -3 groups fall into place quickly."
        )

else:
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
