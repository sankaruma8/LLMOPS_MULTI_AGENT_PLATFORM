# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

This is a college project. It is not intended for production use and receives no
security updates.

## Security Considerations for This Project

- **Never commit `.env`** — it is git-ignored. It contains API keys for Groq,
  OpenAI, Supabase, and Tavily.
- **JWT secret** — set `SECRET_KEY` in `.env` to a long random value. The default
  value is only a placeholder and must be replaced in any shared environment.
- **Supabase keys** — use the **anon/public** key in the frontend; never expose
  the service-role key.
- **CORS** — the API currently allows all origins. For a public deployment this
  should be restricted to your frontend origin.
- **Uploads** — only PDF files are accepted and are stored on the local disk.
  In a shared deployment, limit file size and restrict access.

## Reporting a Vulnerability

Since this is a study project, please report any security issues by opening a
GitHub issue on the repository rather than emailing. There is no SLA or fix
guarantee.
