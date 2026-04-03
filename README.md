# Notes Cleaner Pro

Turn messy notes into clean summaries or CRM-ready records in seconds.

---

## Overview

Notes Cleaner Pro is a lightweight internal tool designed to standardize note-taking and reduce manual cleanup.

Paste rough notes from calls, interviews, or conversations, and generate structured, copy-ready output for Microsoft Teams or email.

---

## Features

* Clean and normalize messy notes automatically
* Expand common shorthand (EM → Emergency Medicine, peds → Pediatrics)
* Generate structured outputs:

  * AI Notes (summary + actions + open items)
  * CRM Format (structured record)
* Copy-ready formatting for:

  * Microsoft Teams (plain text)
  * Email
* Consistent, deterministic output (same input → same result)

---

## Example Use Cases

* Recruiter call notes
* Candidate intake summaries
* Internal status updates
* Preparing CRM entries
* Cleaning up meeting notes

---

## How It Works

1. Paste raw notes (no formatting needed)
2. Select output type (AI Notes or CRM Format)
3. Click **Generate Output**
4. Copy and paste into Teams, email, or your system

---

## Getting Started

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Set your OpenAI API key

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_api_key_here
```

### 3. Run the app

```
python -m streamlit run app.py
```

Then open the local URL in your browser.

---

## Output Types

### AI Notes

* Clean summary
* Key details
* Action items
* Open questions

### CRM Format

* Structured record fields
* Compensation, availability, qualifications
* Next steps
* Missing fields highlighted

---

## Data Handling

* Do not include sensitive personal data (SSN, DOB, full addresses, etc.)
* Outputs are AI-generated and should be reviewed before sending or saving

---

## Tech Stack

* Python
* Streamlit
* OpenAI API

---

## Notes

This is a lightweight internal tool focused on speed and usability.
Designed for real-world workflows, not heavy configuration.

---

## Future Improvements (Optional)

* CRM integration (auto-fill records)
* Role-specific output templates
* Input validation for sensitive data
* Usage analytics

---

## License

Internal use / personal project
