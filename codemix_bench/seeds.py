"""Hand-written seed personas and scenarios.

These are deliberately written by hand (not LLM-generated) so the benchmark has a
trustworthy gold core. Step 2 expands them with an LLM; Step 3 has native speakers
(you + friends) review and fix them.

NOTE: Romanized Telugu/Hindi has no standard spelling. Spelling variation is
expected and is itself something the benchmark should tolerate.
"""
from .schemas import Persona, Scenario

PERSONAS: list[Persona] = [
    # ---------------- Telugu + English ----------------
    Persona(
        id="te01", lang_pair="te-en", script="roman", mix_level=3, formality="casual",
        address_form="nuvvu", age=21, occupation="final-year engineering student",
        region="Bhimavaram, Andhra Pradesh", verbosity="terse", uses_emoji=False,
        sample_utterances=[
            "Bro the assignment deadline is tomorrow and I have no idea em cheyyali.",
            "Can you send the machine learning notes, exam ki time ledu.",
        ],
        memory_facts=["Eats non-veg, loves chicken biryani", "Follows cricket, supports CSK"],
    ),
    Persona(
        id="te02", lang_pair="te-en", script="roman", mix_level=2, formality="polite",
        address_form="meeru", age=33, occupation="software engineer",
        region="Hyderabad, Telangana", verbosity="verbose", uses_emoji=False,
        sample_utterances=[
            "Office lo kotha project start chesam, kani team alignment konchem kastam ga undi. Meeru emanna suggest cheyagalara?",
            "Naku weekend lo family tho ekkadaina short trip plan cheyyali, maa papa ki 5 years.",
        ],
        memory_facts=["Vegetarian", "Has a 5-year-old daughter", "Commutes by metro"],
    ),
    Persona(
        id="te03", lang_pair="te-en", script="native_mixed", mix_level=1, formality="formal",
        address_form="meeru", age=54, occupation="homemaker",
        region="Guntur, Andhra Pradesh", verbosity="medium", uses_emoji=False,
        sample_utterances=[
            "నాకు ఈ phone లో WhatsApp ఎలా use చేయాలో కొంచెం చెప్పండి.",
            "మా అమ్మాయి Bengaluru లో ఉంటుంది, ఆమెకి video call ఎలా చేయాలి?",
        ],
        memory_facts=["Vegetarian", "Daughter lives in Bengaluru", "Prefers Telugu script"],
    ),
    Persona(
        id="te04", lang_pair="te-en", script="roman", mix_level=3, formality="casual",
        address_form="nuvvu", age=19, occupation="first-year BSc student",
        region="Visakhapatnam, Andhra Pradesh", verbosity="medium", uses_emoji=True,
        sample_utterances=[
            "Bro this weekend Vizag beach plan cheddam, any ideas? \U0001F604",
            "Recommend some good anime, new series start cheyyali anukuntunna \U0001F525",
        ],
        memory_facts=["Loves anime", "Gets seasick, avoids boat rides"],
    ),
    # ---------------- Hindi + English ----------------
    Persona(
        id="hi01", lang_pair="hi-en", script="roman", mix_level=3, formality="casual",
        address_form="tum", age=20, occupation="college student",
        region="Delhi", verbosity="terse", uses_emoji=False,
        sample_utterances=[
            "Bro I have an assignment due tomorrow and I'm totally stuck, kuch samajh nahi aa raha.",
            "Can you make my resume for the placement drive, jaldi chahiye.",
        ],
        memory_facts=["Eats non-veg", "Takes the metro to college"],
    ),
    Persona(
        id="hi02", lang_pair="hi-en", script="roman", mix_level=2, formality="formal",
        address_form="aap", age=32, occupation="product manager",
        region="Mumbai, Maharashtra", verbosity="medium", uses_emoji=False,
        sample_utterances=[
            "Mujhe apne manager ko leave ke liye ek email likhna hai, thoda formal tone mein.",
            "Kya aap mujhe quarterly review ke liye ek short agenda suggest kar sakte hain?",
        ],
        memory_facts=["Vegetarian (Jain, no onion or garlic)", "Works hybrid, three days in office"],
    ),
    Persona(
        id="hi03", lang_pair="hi-en", script="native_mixed", mix_level=1, formality="polite",
        address_form="aap", age=55, occupation="retired government clerk",
        region="Lucknow, Uttar Pradesh", verbosity="medium", uses_emoji=False,
        sample_utterances=[
            "मुझे अपने बेटे के लिए एक अच्छा laptop चाहिए, budget 50 हज़ार है।",
            "Bank की app में पैसे भेजने का तरीका आप आसान भाषा में बता दीजिए।",
        ],
        memory_facts=["Prefers less spicy food", "Son is starting college this year", "Prefers Devanagari script"],
    ),
    Persona(
        id="hi04", lang_pair="hi-en", script="roman", mix_level=2, formality="casual",
        address_form="tu", age=24, occupation="freelance designer",
        region="Jaipur, Rajasthan", verbosity="medium", uses_emoji=True,
        sample_utterances=[
            "Bhai weekend pe Jaipur mein kuch naya try karna hai, suggestions de na \U0001F60E",
            "Client ka payment late ho raha hai, usko polite reminder kaise bhejun?",
        ],
        memory_facts=["Vegetarian", "Rides a scooter", "Works from cafes"],
    ),
]

SCENARIOS: list[Scenario] = [
    Scenario(
        id="s01_interview_nerves", domain="emotional support / career",
        description="User has a mock interview tomorrow and feels nervous; wants practical tips.",
        seed_messages={
            "hi-en": "Kal mera mock interview hai aur mujhe bahut nervous feel ho raha hai. Kuch tips do na.",
            "te-en": "Repu naaku mock interview undi, chala nervous ga undi. Konni tips cheppandi.",
        },
        checks=["lang_match", "mix_level_match", "address_form", "helpfulness"],
    ),
    Scenario(
        id="s02_recipe", domain="food / culture",
        description="User wants a simple weekend recipe. Tests dietary memory and regional dishes.",
        seed_messages={
            "hi-en": "Weekend pe kuch special banana hai, ek simple recipe batao.",
            "te-en": "Weekend ki em special cheyyalani undi, oka simple recipe cheppandi.",
        },
        checks=["cultural_fit", "preference_use", "lang_match", "helpfulness"],
        needs_memory=True,
        notes="A non-veg recipe for a vegetarian persona is a hard failure on preference_use.",
    ),
    Scenario(
        id="s03_message_to_elder", domain="interpersonal / honorifics",
        description="User wants to draft a WhatsApp message to a grandfather about visiting for a festival.",
        seed_messages={
            "hi-en": "Dada ji ko WhatsApp pe message bhejna hai ki main festival pe aa raha hoon. Draft kar do.",
            "te-en": "Thatha garu ki WhatsApp lo message pampali, festival ki vastunnanu ani. Draft cheyyandi.",
        },
        checks=["address_form", "cultural_fit", "lang_match", "mix_level_match"],
        notes="The draft must use respectful forms for the elder (aap / meeru-garu) even if the user is casual.",
    ),
    Scenario(
        id="s04_study_plan", domain="education",
        description="User has exams in two weeks and wants a study plan.",
        seed_messages={
            "hi-en": "Do hafte mein exams hain, ek study plan bana do jo realistic ho.",
            "te-en": "Rendu vaaralu lo exams unnayi, oka realistic study plan cheyyandi.",
        },
        checks=["lang_match", "mix_level_match", "helpfulness"],
    ),
    Scenario(
        id="s05_explain_concept", domain="technical explanation",
        description="User asks what gradient descent is, in simple words.",
        seed_messages={
            "hi-en": "Gradient descent kya hota hai? Simple language mein samjhao.",
            "te-en": "Gradient descent ante enti? Simple ga cheppandi.",
        },
        checks=["lang_match", "mix_level_match", "script_match", "helpfulness"],
        notes="Technical terms should stay in English; explanation glue should follow the user's mix level.",
    ),
    Scenario(
        id="s06_budget", domain="personal finance",
        description="User with a modest monthly income wants a simple budget split.",
        seed_messages={
            "hi-en": "Meri monthly income 30,000 hai, budget kaise banaun? Simple split bata do.",
            "te-en": "Naa monthly income 30,000, budget ela plan cheyyali? Simple split cheppandi.",
        },
        checks=["lang_match", "cultural_fit", "helpfulness"],
        notes="Check for India-relevant categories (rent, UPI spends, festivals, family) over generic Western ones.",
    ),
    Scenario(
        id="s07_weekend_plan", domain="travel / local context",
        description="User wants a weekend plan near their city. Tests local knowledge and memory.",
        seed_messages={
            "hi-en": "Is weekend kahin ghoomne jaana hai, koi achha plan suggest karo.",
            "te-en": "Ee weekend ekkadaina ventane vellali, oka manchi plan suggest cheyyandi.",
        },
        checks=["cultural_fit", "preference_use", "lang_match", "helpfulness"],
        needs_memory=True,
        notes="Plan should start from the persona's region and respect stored constraints (e.g. seasickness).",
    ),
    Scenario(
        id="s08_tech_help", domain="everyday tech help",
        description="User needs step-by-step help with a common phone or banking task.",
        seed_messages={
            "hi-en": "Phone se UPI payment kaise karte hain? Step by step bata do.",
            "te-en": "Phone nundi UPI payment ela chestaro step by step cheppandi.",
        },
        checks=["lang_match", "script_match", "mix_level_match", "address_form", "helpfulness"],
        notes="Tests whether register and script match a low-mix, native-script user versus a high-mix roman user.",
    ),
]
