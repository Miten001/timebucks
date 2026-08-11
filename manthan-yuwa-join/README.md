# Manthan4Yuva — Join Page (Faithful Recreation)

A faithful recreation of the **Manthan4Yuva Nagpur 2026** participant registration page
(https://manthan4yuwa.janmanthan.org/#/join), matching the original's tricolor theme,
layout, and multi-step registration flow.

## Matches the original
- **Theme:** saffron `#F24805`, India green `#078929`, deep navy `#06165A`, warm cream
  surfaces, over a dark navy hero with glowing saffron/blue accents. Inter font.
- **Top navigation:** Home · About Us · Timeline · Competition · Join · EN|म toggle, with
  the "म" Jan Manthan Foundation logo.
- **Hero:** MANTHAN4YUVA · NAGPUR 2026 · LEARN • LEAD • CREATE • SERVE.
- **3-step registration wizard:**
  1. OTP Verification (name + WhatsApp mobile + Send OTP + Verify) — demo OTP `123456`
  2. Select Event
  3. Registration Details (email, city, school/college)
- **Tabs:** New Registration / Already Registered?
- **Sidebar:** Participant "SCAN HERE" QR + Convenors (Vishnu Changde, Ritesh Gawande).
- **Footer:** Jan Manthan Foundation · One City. One Movement. One Future. ·
  युवा शक्ती महाराष्ट्राची प्रगति · Maharashtra's Future Through Youth ·
  Developed by Ziplink Consultancy Pvt Ltd.

## Tech
Single self-contained `index.html` (embedded CSS + JS, no build step). Open directly in a browser.
Signups are saved to `localStorage` (key `m4y_registrations`). Fully responsive.

> The Select Event options are representative placeholders; the real event list and the live
> OTP backend can be wired in later. All other content/branding matches the original.
