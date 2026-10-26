import json
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings
from app.models.models import Lead, WebsiteAudit
from app.models.enums import OutreachChannel, OutreachLanguage


async def call_optional_llm(prompt: str) -> Optional[str]:
    """Optional LLM adapter for OpenAI / Gemini API if configured."""
    if settings.OPENAI_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": "You are a professional B2B marketing outreach specialist. Strictly adhere to provided facts. Never fabricate statistics, prior interactions, or non-existent company problems."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.4
                    }
                )
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"]
        except Exception:
            pass

    if settings.GEMINI_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                res = await client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}]
                    }
                )
                if res.status_code == 200:
                    return res.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            pass

    return None


def generate_outreach_draft_template(
    lead: Lead,
    audit: Optional[WebsiteAudit],
    channel: str,
    language: str = "en",
    custom_instructions: Optional[str] = None
) -> Dict[str, Any]:
    """
    High-converting, template-based personalized outreach generator.
    Works 100% free without paid AI keys.
    Grounds message strictly in verified data without fabricating claims.
    """
    company = lead.company_name
    contact = lead.publicly_listed_contact_name or "Team"
    city = lead.city or "your area"
    industry = lead.industry or "local businesses"
    service = lead.recommended_service or "Digital Marketing & SEO"

    # Compile verified evidence
    evidence_points = []
    if not lead.official_website:
        evidence_points.append("no public website could be verified for your business")
    elif audit:
        if not audit.is_https:
            evidence_points.append(f"your website ({lead.official_website}) currently runs on unencrypted HTTP without SSL")
        if not audit.has_viewport:
            evidence_points.append("your site lacks a mobile viewport tag, leading to sizing issues on smartphones")
        if not audit.page_title:
            evidence_points.append("the homepage is missing a descriptive search title tag")
        if not audit.meta_description:
            evidence_points.append("no search snippet meta description is configured for Google results")
        if audit.images_missing_alt_count > 0:
            evidence_points.append(f"{audit.images_missing_alt_count} website images lack accessibility alt descriptions")
        if not audit.has_contact_page:
            evidence_points.append("no direct contact link is highlighted in the top navigation")

    primary_evidence = evidence_points[0] if evidence_points else f"enhancing online visibility for {industry} in {city}"
    evidence_str = f"Specific evidence verified: {primary_evidence}."

    # English Templates
    if language == OutreachLanguage.EN.value:
        if channel == OutreachChannel.COLD_EMAIL.value:
            subject = f"Quick question regarding {company}'s online visibility in {city}"
            body = (
                f"Hi {contact},\n\n"
                f"I was recently researching leading {industry} providers in {city} and came across {company}.\n\n"
                f"While reviewing your public online presence, I noticed that {primary_evidence}. In a competitive market like {city}, this can result in missed inquiries from prospective clients searching online.\n\n"
                f"We specialize in {service} for {industry} firms, helping businesses convert search traffic into booked clients.\n\n"
                f"Would you be open to a quick 10-minute introductory call this Thursday to review our detailed audit findings?\n\n"
                f"Best regards,\n"
                f"LeadGen Lite Growth Team"
            )
            next_action = "Schedule follow-up reminder for 3 business days if no reply."

        elif channel == OutreachChannel.FOLLOW_UP_EMAIL.value:
            subject = f"Following up: {company} digital growth review"
            body = (
                f"Hi {contact},\n\n"
                f"Following up briefly on my earlier note regarding {company}'s digital setup in {city}.\n\n"
                f"We prepared a complimentary action plan focusing on {service} to address the finding that {primary_evidence}.\n\n"
                f"Would 10:00 AM on Tuesday work for a quick screen share, or would later in the week suit you better?\n\n"
                f"Best regards,\n"
                f"LeadGen Lite Growth Team"
            )
            next_action = "Track reply or move to LinkedIn touchpoint."

        elif channel == OutreachChannel.LINKEDIN_NOTE.value:
            subject = "LinkedIn Connection Request"
            # Strict limit: Under 300 characters
            body = (
                f"Hi {contact}, noticed {company}'s great work in {city}. "
                f"Did a quick digital audit and spotted an opportunity in {service}. "
                f"Would love to connect here!"
            )[:295]
            next_action = "Send personalized connection request on LinkedIn."

        elif channel == OutreachChannel.LINKEDIN_DRAFT.value:
            subject = f"Connecting regarding {company}"
            body = (
                f"Hi {contact},\n\n"
                f"Hope your week is off to a productive start. I came across {company} while reviewing {industry} firms in {city}.\n\n"
                f"I put together a quick technical review of your online assets and noted that {primary_evidence}.\n\n"
                f"We frequently help teams in your sector implement {service} to capture high-intent local demand. I'd be glad to send over a 2-page breakdown if you're interested.\n\n"
                f"Best,\n"
                f"Growth Team"
            )
            next_action = "Send via LinkedIn InMail or Message once connection is accepted."

        elif channel == OutreachChannel.WHATSAPP_DRAFT.value:
            subject = None
            body = (
                f"Hello {contact}! Greetings from the LeadGen Growth Team.\n\n"
                f"We recently reviewed {company}'s online presence in {city} and identified a quick improvement opportunity: {primary_evidence}.\n\n"
                f"We assist {industry} businesses with {service}. If you'd like a quick complimentary summary of the findings, let us know and we'll share it here!\n\n"
                f"Have a great day ahead."
            )
            next_action = "Verify WhatsApp opt-in eligibility before sending."
        else:
            subject = f"Opportunity for {company}"
            body = f"Hello {contact}, we identified an opportunity regarding {service} for {company}."
            next_action = "Review draft manually."

    # Hindi Templates (Natural, respectful business Hindi)
    else:
        if channel == OutreachChannel.COLD_EMAIL.value:
            subject = f"{company} के डिजिटल विकास और ऑनलाइन विजिबिलिटी के संबंध में"
            body = (
                f"नमस्ते {contact},\n\n"
                f"आशा है आप सकुशल होंगे। हमने {city} में {industry} क्षेत्र में {company} के कार्य को देखा।\n\n"
                f"आपकी ऑनलाइन उपस्थिति का विश्लेषण करते समय हमें ज्ञात हुआ कि {primary_evidence}। आज के प्रतिस्पर्धी बाजार में, इससे कई संभावित ग्राहक छूट सकते हैं।\n\n"
                f"हम {industry} क्षेत्र के व्यवसायों के लिए {service} में विशेषज्ञता रखते हैं, जिससे ऑनलाइन पूछताछ और व्यवसाय में वृद्धि होती है।\n\n"
                f"क्या हम इस सप्ताह 10 मिनट की एक संक्षिप्त चर्चा कर सकते हैं?\n\n"
                f"सादर,\n"
                f"लीडजेन ग्रोथ टीम"
            )
            next_action = "3 कार्य दिवसों के बाद फॉलो-अप निर्धारित करें।"

        elif channel == OutreachChannel.FOLLOW_UP_EMAIL.value:
            subject = f"फॉलो-अप: {company} की डिजिटल ऑडिट रिपोर्ट"
            body = (
                f"नमस्ते {contact},\n\n"
                f"मैं अपने पिछले ईमेल के संदर्भ में संपर्क कर रहा हूँ। हमने {company} के लिए {service} पर केंद्रित एक निःशुल्क कार्य योजना तैयार की है।\n\n"
                f"क्या इस सप्ताह आपके पास 10 मिनट का समय होगा ताकि हम मुख्य बिंदु साझा कर सकें?\n\n"
                f"सादर,\n"
                f"लीडजेन ग्रोथ टीम"
            )
            next_action = "उत्तर की प्रतीक्षा करें या लिंक्डइन पर संपर्क करें।"

        elif channel == OutreachChannel.LINKEDIN_NOTE.value:
            subject = "लिंक्डइन कनेक्शन अनुरोध"
            body = (
                f"नमस्ते {contact}, {city} में {company} के कार्य को देखा। "
                f"आपकी डिजिटल उपस्थिति में {service} के लिए कुछ महत्वपूर्ण सुधार बिंदु देखे। "
                f"आपसे यहाँ जुड़ना सम्मान की बात होगी!"
            )[:295]
            next_action = "लिंक्डइन पर कनेक्शन अनुरोध भेजें।"

        elif channel == OutreachChannel.LINKEDIN_DRAFT.value:
            subject = f"{company} के विकास हेतु संवाद"
            body = (
                f"नमस्ते {contact},\n\n"
                f"आशा है आपका सप्ताह अच्छा चल रहा होगा। हमने {city} में {industry} कंपनियों के विश्लेषण के दौरान {company} को देखा।\n\n"
                f"आपकी वेबसाइट और ऑनलाइन उपस्थिति के दौरान हमने पाया कि: {primary_evidence}।\n\n"
                f"हम {service} के माध्यम से स्थानीय स्तर पर नए ग्राहक प्राप्त करने में मदद करते हैं। यदि आप रुचि रखते हैं, तो मैं एक संक्षिप्त रिपोर्ट साझा कर सकता हूँ।\n\n"
                f"सादर,\n"
                f"ग्रोथ टीम"
            )
            next_action = "कनेक्शन स्वीकार होने पर लिंक्डइन मैसेज भेजें।"

        elif channel == OutreachChannel.WHATSAPP_DRAFT.value:
            subject = None
            body = (
                f"नमस्ते {contact}! लीडजेन ग्रोथ टीम की ओर से नमस्कार।\n\n"
                f"हमने {city} में {company} की ऑनलाइन विजिबिलिटी की समीक्षा की और पाया कि: {primary_evidence}।\n\n"
                f"हम {industry} व्यवसायों को {service} द्वारा नए ग्राहक आकर्षित करने में मदद करते हैं। यदि आप चाहें, तो हम संक्षिप्त ऑडिट रिपोर्ट यहीं साझा कर सकते हैं।\n\n"
                f"आपका दिन शुभ हो!"
            )
            next_action = "व्हाट्सएप ऑप्ट-इन की पुष्टि करें।"
        else:
            subject = f"{company} के लिए अवसर"
            body = f"नमस्ते {contact}, हमने {company} के लिए {service} का एक महत्वपूर्ण अवसर पहचाना है।"
            next_action = "ड्राफ्ट की समीक्षा करें।"

    return {
        "channel": channel,
        "language": language,
        "subject_line": subject,
        "message_body": body.strip(),
        "recommended_service": service,
        "personalization_evidence": evidence_str,
        "suggested_next_action": next_action
    }
