import reflex as rx
import asyncio
from typing import TypedDict
from app.states.medicine_state import MedicineState


class ChatMessage(TypedDict):
    role: str
    content: str


class ChatState(rx.State):
    messages: list[ChatMessage] = [
        {
            "role": "bot",
            "content": "👋 Hi there! I'm your MediSmart Assistant. I can help you understand generic medicines, prescription terms, or find affordable alternatives. What would you like to know?",
        }
    ]
    is_chat_open: bool = False
    current_message: str = ""
    is_typing: bool = False
    suggested_questions: list[str] = [
        "Analyze Crocin 500mg",
        "Compare alternatives for Pan 40",
        "Is Augmentin 625 safe to substitute?",
        "What are generic medicines?",
        "How much can I save with generics?",
        "Analyze Thyronorm 50",
        "Find alternatives for Glycomet 500",
        "What is bioequivalence?",
    ]

    @rx.event
    def toggle_chat(self):
        self.is_chat_open = not self.is_chat_open
        if self.is_chat_open:
            yield rx.call_script(
                "setTimeout(() => { const el = document.getElementById('chat-messages'); if(el) el.scrollTop = el.scrollHeight; }, 100);"
            )

    @rx.event
    def set_current_message(self, message: str):
        self.current_message = message

    async def _generate_response(self, user_text: str) -> str:
        """Helper to generate a response based on user input."""
        await asyncio.sleep(0.8)
        lower_text = user_text.lower()
        response = ""
        from app.states.medicine_state import MEDICINE_DATABASE

        found_med_key = None
        for key, data in MEDICINE_DATABASE.items():
            if data["brand_name"].lower() in lower_text or key in lower_text:
                found_med_key = key
                break
        if found_med_key:
            med = MEDICINE_DATABASE[found_med_key]
            alt_lines = []
            for i, alt in enumerate(med["alternatives"], 1):
                savings_val = med["price_original"] - alt["price"]
                alt_lines.append(
                    f"│ {i} │ {alt['name'][:15].ljust(15)} │ {alt['type'][:14].ljust(14)} │ ₹{str(alt['price'])[:5].ljust(5)} │ ₹{str(savings_val)[:5].ljust(5)} │"
                )
            alts_table = """
""".join(alt_lines)
            best_value = min(med["alternatives"], key=lambda x: x["price"])
            savings = med["price_original"] - med["price_cheapest_safe"]
            pct = (
                round(savings / med["price_original"] * 100)
                if med["price_original"]
                else 0
            )
            savings_warning = (
                f"\n   ⚠️ A verified equivalent exists at {pct}% lower cost!"
                if pct > 50
                else ""
            )
            response = f"🔬 MediCompare AI Analysis: {med['brand_name']}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📋 STEP 1 — MEDICINE IDENTIFICATION\n• Brand: {med['brand_name']}\n• Active Ingredient: {med['active_ingredients']}\n• Form: {med['dosage_form']} | Category: {med['therapeutic_category']}\n• How it works: {med['mechanism']}\n• Standard use: {med['standard_use']}\n\n✅ STEP 2 — REGULATORY VERIFICATION\n• CDSCO Approved: {('✅ Yes' if med['cdsco_approved'] else '❌ No')}\n• NLEM Listed: {('✅' if med['nlem_listed'] else '❌')}\n• Jan Aushadhi: {med['jan_aushadhi_available']}\n• Manufacturing: {med['manufacturing_tier']}\n• ⚠️ Warnings: {med['regulatory_warnings']}\n• Safety Score: {med['safety_score']}/100\n\n💊 STEP 3 — GENERIC ALTERNATIVES\n┌────────────────────────────────────────────────────────┐\n│ # │ Name            │ Type           │ Price   │ Savings │\n{alts_table}\n│ ⭐ Best Value: {best_value['name']} \n└────────────────────────────────────────────────────────┘\n\n💰 STEP 4 — PRICE INTELLIGENCE\n• Original Price: ₹{med['price_original']}/strip\n• Cheapest Safe Generic: ₹{med['price_cheapest_safe']}/strip\n• You Save: ₹{savings} per strip ({pct}%)\n• Annual Savings: ₹{med['annual_savings_estimate']} (for regular use)\n• {med['affordability_tier']}{savings_warning}\n\n🏥 STEP 5 — PHARMACY AVAILABILITY\nSearch for nearby pharmacies stocking this generic on our Pharmacy Locator page → /locator\n\n🚦 STEP 6 — SUBSTITUTION SAFETY\n{med['substitution_safety']}\n{med['substitution_note']}\n\n📝 STEP 7 — PATIENT SUMMARY\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💊 {med['therapeutic_category']} medication for {med['standard_use'].split('.')[0].lower()}.\n💰 Cheapest safe alternative: {best_value['name']} at ₹{best_value['price']} (save ₹{savings})\n🏥 Find it at your nearest Jan Aushadhi Kendra or pharmacy\n⚠️ {med['regulatory_warnings'].split('.')[0]}\n🔔 Always confirm substitutions with your doctor or pharmacist before switching."
            return response
        if "generic" in lower_text and (
            "what" in lower_text or "brand" in lower_text or "difference" in lower_text
        ):
            response = "Generics contain the exact same active ingredient (API/salt), same dosage, and same route of administration as brand-name drugs. They differ only in brand name, packaging, and price. For example, Crocin and generic Paracetamol both contain 500mg of Paracetamol, but have very different prices! 💊"
        elif any(
            (
                w in lower_text
                for w in ["save", "cost", "price", "cheap", "expensive", "savings"]
            )
        ):
            response = "💰 You can typically save 30% to 80% by switching to generic medicines! Jan Aushadhi Kendras offer medicines at 50-90% less than market rates. Fun fact: India's pharmaceutical industry is the world's largest generic supplier!"
        elif any(
            (
                w in lower_text
                for w in ["safe", "quality", "cdsco", "fda", "who", "trust"]
            )
        ):
            response = "✅ Yes, generic medicines are equally safe and effective! They are strictly regulated by CDSCO (India's drug regulator), must pass bioequivalence tests, and are manufactured in WHO-GMP certified facilities. They are widely endorsed by doctors worldwide."
        elif (
            "prescription" in lower_text
            or "read" in lower_text
            or "od" in lower_text
            or ("bd" in lower_text)
            or ("tds" in lower_text)
        ):
            response = """Here are common prescription terms to know:
• OD: Once daily
• BD/BID: Twice daily
• TDS/TID: Three times daily
• QID: Four times daily
• SOS: As needed
• AC: Before food
• PC: After food
• HS: At bedtime 📝"""
        elif "salt" in lower_text or "api" in lower_text or "composition" in lower_text:
            response = "The 'salt' or API (Active Pharmaceutical Ingredient) is the actual chemical that treats your condition. For example, Paracetamol is the salt, while Crocin, Dolo, and Calpol are just different brand names selling the exact same salt! 🧪"
        elif (
            "jan aushadhi" in lower_text
            or "pmbjp" in lower_text
            or "government" in lower_text
        ):
            response = "🏥 The Pradhan Mantri Bhartiya Janaushadhi Pariyojana (PMBJP) is a government initiative providing high-quality generic medicines at affordable prices. There are over 9,000+ dedicated Jan Aushadhi stores across India where you can buy these medicines."
        elif "bioequivalence" in lower_text:
            response = "🔬 Bioequivalence means that the generic drug delivers the exact same amount of active ingredient into your bloodstream, at the exact same rate, as the original brand-name drug. This ensures it works exactly the same way in your body!"
        elif "online" in lower_text or "buy" in lower_text or "internet" in lower_text:
            response = """🛒 Tips for buying medicines online:
1. Always check the expiry date on delivery.
2. Verify the platform has a valid drug license.
3. Compare prices across multiple apps.
4. Stick to well-known generic manufacturers."""
        elif (
            "store" in lower_text or "storage" in lower_text or "sunlight" in lower_text
        ):
            response = "Proper medicine storage is crucial! 🌡️ Store most medicines in a cool, dry place away from direct sunlight and moisture (avoid the bathroom cabinet). Always check the label for specific temperature requirements, and keep them out of children's reach."
        elif (
            "side effect" in lower_text
            or "reaction" in lower_text
            or "allergy" in lower_text
        ):
            response = "⚠️ All medicines (whether brand or generic) can have side effects. Always read the information leaflet and consult your doctor if you experience unusual symptoms. Never self-medicate, especially with antibiotics!"
        elif any((w in lower_text for w in ["hello", "hi", "hey", "greetings"])):
            response = "Hello! 👋 I'm here to help you navigate the world of affordable medicines. You can ask me about generic alternatives, how to read prescriptions, or medicine safety."
        elif any((w in lower_text for w in ["thank", "thanks", "helpful", "great"])):
            response = "You're very welcome! 😊 Feel free to use the Search or Upload Prescription features to find specific affordable alternatives. Stay healthy!"
        else:
            response = "I can help with questions about generic medicines, savings, prescription reading, medicine safety, and finding affordable alternatives. Could you rephrase your question? 🩺"
        return response

    @rx.event
    async def send_suggested_question(self, question: str):
        """Send a suggested question directly without relying on form submission."""
        self.messages.append({"role": "user", "content": question})
        self.current_message = ""
        self.is_typing = True
        yield
        yield rx.call_script(
            "setTimeout(() => { const el = document.getElementById('chat-messages'); if(el) el.scrollTop = el.scrollHeight; }, 50);"
        )
        response = await self._generate_response(question)
        self.messages.append({"role": "bot", "content": response})
        self.is_typing = False
        yield
        yield rx.call_script(
            "setTimeout(() => { const el = document.getElementById('chat-messages'); if(el) el.scrollTop = el.scrollHeight; }, 50);"
        )

    @rx.event
    async def send_message(self, form_data: dict[str, str]):
        """Handle message submission from the chat input form."""
        user_text = form_data.get("message", "").strip()
        if not user_text:
            return
        self.messages.append({"role": "user", "content": user_text})
        self.current_message = ""
        self.is_typing = True
        yield
        yield rx.call_script(
            "setTimeout(() => { const el = document.getElementById('chat-messages'); if(el) el.scrollTop = el.scrollHeight; }, 50);"
        )
        response = await self._generate_response(user_text)
        self.messages.append({"role": "bot", "content": response})
        self.is_typing = False
        yield
        yield rx.call_script(
            "setTimeout(() => { const el = document.getElementById('chat-messages'); if(el) el.scrollTop = el.scrollHeight; }, 50);"
        )