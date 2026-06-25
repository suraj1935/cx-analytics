"""Create or reset a Supabase Auth admin user for local development.

Usage:
    python scripts/create_admin_user.py admin@example.com "StrongPassword123!"
"""

import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from supabase import create_client


def main() -> int:
    if len(sys.argv) != 3:
        print('Usage: python scripts/create_admin_user.py <email> "<password>"')
        return 2

    email = sys.argv[1].strip()
    password = sys.argv[2]
    if "@" not in email or len(password) < 8:
        print("Email must be valid and password must be at least 8 characters.")
        return 2

    backend_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend_dir))

    env_path = backend_dir / ".env"
    load_dotenv(env_path)

    from app.config import settings

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        print("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in backend/.env")
        return 1

    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    try:
        users = supabase.auth.admin.list_users()
    except httpx.ConnectError as exc:
        host = urlparse(settings.SUPABASE_URL).netloc or settings.SUPABASE_URL
        masked_host = f"{host[:6]}...{host[-18:]}" if len(host) > 26 else host
        print(f"Could not reach Supabase project host: {masked_host}")
        print("Check SUPABASE_URL in backend/.env. It must exactly match Project Settings > API > Project URL.")
        return 1
    existing = next((user for user in users if user.email and user.email.lower() == email.lower()), None)

    if existing:
        supabase.auth.admin.update_user_by_id(
            existing.id,
            {
                "password": password,
                "email_confirm": True,
                "user_metadata": {"role": "admin"},
            },
        )
        print(f"Updated existing Supabase Auth user: {email}")
        return 0

    supabase.auth.admin.create_user(
        {
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"role": "admin"},
        }
    )
    print(f"Created Supabase Auth user: {email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
