# AI Personal Journal & Mood Intelligence System

A portfolio-quality digital journal web application that starts with personal daily journaling and manual emotional state tracking, designed to evolve into an AI-powered mood intelligence system.

---

## Roadmap

- **V1 - Smart Journal (Current Foundation)**: Core digital journal with manual emotion tracking (Happy, Neutral, Sad, Angry, Stressed), user authentication, and basic dashboard metrics.
- **V2 - AI Emotion & Mood Analysis**: Analyze journal text for sentiment, emotion, mood intensity, and topics.
- **V3 - Personal Insights**: Analyze historical entries to discover emotional patterns and trends over time.
- **V4 - Voice + Multimodal Analysis**: Combine speech-to-text, prosody analysis, and multimodal inputs.

---

## Tech Stack

- **Backend**: Python, Flask (Application Factory & Blueprints)
- **Database / ORM**: SQLite, SQLAlchemy, Flask-SQLAlchemy
- **Authentication**: Flask-Login, Werkzeug security password hashing
- **Frontend**: Jinja2 Templates, Semantic HTML5, CSS3, Modern JavaScript
- **Testing**: pytest
- **Package & Environment Manager**: uv

---

## Project Structure

```
ai-personal-journal/
├── .github/
│   └── workflows/
├── app/
│   ├── auth/
│   ├── dashboard/
│   ├── journal/
│   ├── static/
│   │   ├── css/
│   │   ├── images/
│   │   └── js/
│   └── templates/
│       ├── auth/
│       ├── dashboard/
│       └── journal/
├── tests/
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml
└── uv.lock
```

---

## Git Workflow & Branching Strategy

- `main` &mdash; Stable/production-ready code.
- `develop` &mdash; Integration branch for ongoing development.
- `feature/<developer>/<feature>` &mdash; Feature development branches (e.g., `feature/devansh/journal-crud`).
- `bugfix/<developer>/<bug>` &mdash; Bug fix branches.

### Workflow:
`feature branch` &rarr; `Pull Request` &rarr; `Code Review` &rarr; `develop` &rarr; `Testing` &rarr; `main`

---

## Getting Started

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (Fast Python package and environment manager)
- Python 3.11+

### Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai-personal-journal
   ```

2. **Set up the virtual environment and install dependencies with `uv`**:
   ```bash
   uv sync --all-extras
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env` (or configure your environment):
   ```bash
   cp .env.example .env
   ```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
