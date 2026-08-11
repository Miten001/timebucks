# Manthan 4 Yuwa — Join Page (Rich Color Recreation)

A vibrant, gradient-driven recreation of the **Manthan 4 Yuwa** youth-community join / registration page.

## What it is
A single self-contained `index.html` (embedded CSS + JS, no build step). Just open it in a browser.

## Features
- Bold hero section with animated color blobs and gradient text.
- Glassmorphism registration form capturing **name, email, phone, city**.
- Layered validation: inline field-level checks on blur + full-form check on submit.
- Input normalization (trim, lowercase email, digit-normalize phone) before saving.
- Front-end persistence via `localStorage` (key: `m4y_registrations`).
- Rich color theme: magenta-pink, electric violet, sunny amber, cyan over deep indigo.
- Success + error states with light-touch animation. Fully responsive.

## How to view
Open `manthan-yuwa-join/index.html` directly in any modern browser.

> Note: hero copy is placeholder text since the original SPA content could not be scraped. Swap in your exact wording anytime.
