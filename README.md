# Aurora Scholar

Aurora Scholar is a bilingual educational platform that combines diagnostics, personalised study plans, and an AI tutor across four core subjects: mathematics, Russian, English, and physics.

## Features

- Account system with registration, login, logout, and preference management.
- Diagnostics quizzes for each subject to determine skill level before starting the learning plan.
- Automatic study plan generation aligned with beginner, intermediate, or advanced levels for every subject.
- Integrated AI assistant that uses an OpenAI ChatGPT token supplied by the user to deliver teacher-style guidance.
- Interface language selection (Russian or English) per user.
- Responsive visual design based on Bootstrap 5 with custom gradients and chat styling.

## Getting started

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the development server**
   ```bash
   flask --app app run --debug
   ```

   The application uses an SQLite database stored in `instance/aurora.db`. Tables are created automatically on first launch.

3. **Configure the AI tutor**
   - Register or log in and open the *Settings* page.
   - Paste your OpenAI API token. The token is stored locally in the SQLite database.
   - Navigate to the *AI Tutor* page and ask questions. The assistant prompt encourages detailed, supportive explanations.

## Project structure

```
app.py               # Flask application entry point
translations.py      # UI translations for English and Russian
diagnostics.py       # Quiz definitions, study plan library, and tutor prompt
database.py          # SQLite helpers and schema
/templates           # Jinja templates for all pages
/static              # Custom CSS
```

## Safety note

The repository stores the API token in plain text within the local database for simplicity. For production use, employ encryption or a secure secrets manager.
