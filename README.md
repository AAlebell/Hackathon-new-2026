# 🛡️ Chatbot Defense Arena

natHacks 2026, Defense & Security theme.

Small businesses are adding AI chatbots to their websites, and those chatbots can be tricked
into leaking internal information through prompt injection, the number one risk in the OWASP
Top 10 for LLM Applications. Chatbot Defense Arena puts you on the blue team: write the rules
that protect a business chatbot, then watch attackers try to break them while real customers
still need help. You score for every attack blocked **and** every customer served.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
python test_engine.py              # quick engine check, no API cost
streamlit run app.py
```

By default `USE_FAKE_AI=true`, so no API key is needed. To use Gemini, add your key from
Google AI Studio to `.env` and set `USE_FAKE_AI=false`.

## Project structure

```
engine/        game logic (AI calls, judge, rounds, easy mode)
scenarios/     game content as JSON, one file per business
app.py         Streamlit interface
test_engine.py engine checks without the interface
```

## Team

Built during natHacks 2026 (November 6 to 9) at the University of Alberta.
