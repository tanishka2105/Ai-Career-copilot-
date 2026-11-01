<div align="center">

# Ascendra

**Intelligence That Moves You Forward.**

An AI-powered career platform for smarter resumes, personalized insights, and interview readiness.

[![Live Demo](https://img.shields.io/badge/Live_Demo-Open_App-0E7A57?style=for-the-badge)](https://ai-career-copilot-2-pu0m.onrender.com)

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![PWA](https://img.shields.io/badge/Installable-PWA-5A0FC8?style=flat-square)
![Hosted on Render](https://img.shields.io/badge/Hosted_on-Render-46E3B7?style=flat-square&logo=render&logoColor=black)

*The first load can take up to a minute because the app runs on a free hosting plan and wakes up from sleep.*

</div>

---

## Screenshots

<!-- Put your images in docs/screenshots/ with these exact names. Use the same aspect ratio (for example 16:9) for all of them. -->

<p align="center">
  <img src="<img width="1280" height="882" alt="WhatsApp Image 2026-11-01 at 3 07 41 PM" src="https://github.com/user-attachments/assets/512c3056-5f92-4cb3-b566-defcfc93d80f" />
" alt="Ascendra landing page" width="100%">
</p>

<table>
  <tr>
    <td width="50%" align="center">
      <img src="<img width="1280" height="882" alt="WhatsApp Image 2026-11-01 at 3 07 42 PM (1)" src="https://github.com/user-attachments/assets/7f19d4b3-d53e-4a68-80a9-eac89011eea0" />
" alt="Overview" width="100%"><br>
      <sub><b>Overview</b></sub>
    </td>
    <td width="50%" align="center">
      <img src="<img width="1280" height="882" alt="WhatsApp Image 2026-11-01 at 3 07 42 PM (2)" src="https://github.com/user-attachments/assets/e582b179-f2cb-4c47-813f-57e8322d18b7" />
" alt="Resume match" width="100%"><br>
      <sub><b>Resume match</b></sub>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="<img width="1280" height="882" alt="WhatsApp Image 2026-11-01 at 3 07 42 PM" src="https://github.com/user-attachments/assets/388ab540-5352-48fa-9567-fe251090521d" />
" alt="Interview coach" width="100%"><br>
      <sub><b>Interview coach</b></sub>
    </td>
    <td width="50%" align="center">
      <img src="<img width="1280" height="882" alt="WhatsApp Image 2026-11-01 at 3 07 42 PM (3)" src="https://github.com/user-attachments/assets/65348dfe-8196-4067-81cd-a41a5007b813" />
" alt="Knowledge base" width="100%"><br>
      <sub><b>Knowledge base</b></sub>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="<img width="1280" height="882" alt="WhatsApp Image 2026-11-01 at 3 07 43 PM" src="https://github.com/user-attachments/assets/546e6fa0-361c-4324-8053-dc90aceafdb6" />
" alt="Job tracker" width="100%"><br>
      <sub><b>Job tracker</b></sub>
    </td>
    <td width="50%"></td>
  </tr>
</table>

### How it helps you

<!-- Drag and drop your video into the GitHub editor and paste the generated link on its own line below. -->
[![How it helps you](how-it-helps-poster.png)](kling_20261028_VIDEO_A_14_secon_75_0.mp4)

```mermaid
flowchart LR
    U["Browser or PWA"] -->|"REST API + JWT"| A["FastAPI backend"]
    A --> D[("PostgreSQL on Supabase")]
    A --> L["LLM API"]
    U -->|"Google Sign-In"| G["Google Identity"]
    G -->|"ID token"| A
```
---

## Why Ascendra?

Preparing for a job usually means juggling a resume, a job description, practice questions and a calendar in different places. Ascendra puts them in one workspace that shares a single profile, so every tool gets more useful the more you use it.

---

## Features

### Resume
- **Resume match:** compare your resume with a job description and get a match score, strengths, skill gaps and the questions that job is likely to ask.
- **Bullet rewrite and cover letter:** draft both using only what is in your resume and the job description.

### Interview practice
- **Interview coach:** practice one question at a time by text or voice. Choose the round, the level and the language (English or Hinglish).
- **Interview scorecard:** AI-estimated practice feedback with PDF export.
- **Question bank:** ready questions with model answers for behavioral, technical, HR and situational rounds, plus an AI generator for any role.

### Planning and tracking
- **Prep planner:** a day-by-day checklist built from your resume match and interview date.
- **Job tracker:** keep applications, statuses, interview dates and notes in one place.
- **Calendar reminder (.ics) and practice chart** to track progress over time.

### Knowledge base
- Upload your own PDFs and ask questions that are answered from your documents.

### Account and experience
- Google sign-in or username and password, with password reset by email.
- Saved chats, documents and analyses, available on any device.
- Light and dark themes, adjustable text size, voice dictation and read-aloud replies.
- Installable as a Progressive Web App.
- Export your data or delete your account at any time.

---

## How it works

```mermaid
flowchart LR
    U["Browser or PWA"] -->|"REST API + JWT"| A["FastAPI backend"]
    A --> D[("PostgreSQL on Supabase")]
    A --> L["LLM API"]
    U -->|"Google Sign-In"| G["Google Identity"]
    G -->|"ID token"| A
```

1. The frontend is a single-page app served by the backend.
2. FastAPI handles authentication (JWT and Google Sign-In), business logic and database access through SQLAlchemy.
3. Resume analysis, coaching, questions and document answers are generated by an LLM API.
4. Chats, documents and analyses are stored per user in PostgreSQL.

---

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | FastAPI, SQLAlchemy |
| Database | PostgreSQL (Supabase) |
| Auth | JWT, Google Sign-In |
| AI | LLM API |
| Frontend | HTML, CSS, JavaScript (no framework) |
| Icons and fonts | Phosphor Icons, DM Sans, Fraunces |
| PWA | Web app manifest, service worker |
| Hosting | Render |

---

## Run locally

**1. Clone and create a virtual environment**

```bash
git clone <your-repo-url>
cd <your-repo-folder>
python -m venv .venv
```

Activate it:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Create a `.env` file**

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | Secret used to sign login tokens |
| `GOOGLE_CLIENT_ID` | Google Sign-In client ID |
| AI API key | Key for the LLM provider you use |
| `BASE_URL` | Public URL of the app, used in emails |
| `SMTP_*` | Mail settings for password reset |

**4. Start the server**

```bash
uvicorn main:app --reload
```

Then open `http://127.0.0.1:8000`.

---

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

---

## Privacy and security

Resumes are personal data, so privacy is part of the design.

- Documents are used only to answer your own requests.
- You can delete chats, documents or your whole account from Settings, and export your data.
- The service worker never caches API calls, so private data does not sit in a shared cache.
- Never commit your `.env` file.
- The app includes a Privacy Policy and Terms of Use page.

Interview scorecards are AI-estimated practice feedback, not a prediction of real interview results.

---

## Project structure (frontend)

```text
index.html       App shell and all views
style.css        Theme, layout and responsive styles
app.js           Frontend logic
sw.js            Service worker (offline fallback, network first)
manifest.json    PWA manifest
```

---

## Author

Built by **Tanishka**, a Computer Science student focused on generative AI.

- GitHub: `https://github.com/tanishka2105`
- LinkedIn: `www.linkedin.com/in/tanishkachaudhary`

If you found this useful, consider giving the repository a star.
