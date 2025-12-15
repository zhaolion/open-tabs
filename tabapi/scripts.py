"""
TabAPI CLI entry point.

Usage:
    uv run tabapi init admin
"""

import asyncio
import re
from datetime import datetime, timezone

import typer
from pydantic import EmailStr, ValidationError
from sqlalchemy import func, select

app = typer.Typer(
    name="tabapi",
    help="TabAPI CLI - Access large language models with ease.",
)

init_app = typer.Typer(help="Initialization commands")
app.add_typer(init_app, name="init")


def generate_username_from_email(email: str) -> str:
    """
    Generate a username from email address.

    Example: admin@example.com -> admin
    """
    local_part = email.split("@")[0]
    # Clean up: only allow alphanumeric, underscore, hyphen
    username = re.sub(r"[^a-zA-Z0-9_-]", "", local_part)
    # Ensure minimum length
    if len(username) < 3:
        username = f"user_{username}"
    # Truncate if too long (username max 50 chars)
    return username[:50]


def validate_email_format(email: str) -> bool:
    """Validate email format using Pydantic."""
    from pydantic import BaseModel

    class EmailModel(BaseModel):
        email: EmailStr

    try:
        EmailModel(email=email)
        return True
    except ValidationError:
        return False


async def create_super_admin(
    email: str,
    password: str,
    name: str,
) -> None:
    """
    Create a super admin user in the database.

    This function handles:
    1. Email uniqueness check
    2. Username generation and uniqueness check
    3. User creation with ACTIVE status
    4. UserAuthentication creation with EMAIL provider
    5. UserAdminProfile creation with SUPER_ADMIN role
    """
    # Import database dependencies inside the async function
    # to avoid import issues at module level
    from tabapi.app.db.session import async_session
    from tabapi.app.modules.auth.enums import (
        AdminRole,
        AuthProviderType,
        UserStatus,
    )
    from tabapi.app.modules.auth.models import (
        User,
        UserAdminProfile,
        UserAuthentication,
    )
    from tabapi.app.modules.auth.utils.password import hash_password
    from tabapi.app.modules.auth.utils.uid import generate_uid

    async with async_session() as session:
        async with session.begin():
            # Check if email already exists
            stmt = select(User).where(func.lower(User.email) == email.lower())
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                typer.echo(
                    typer.style(
                        f"Error: Email '{email}' is already registered.",
                        fg=typer.colors.RED,
                    )
                )
                raise typer.Exit(code=1)

            # Generate and validate username
            base_username = generate_username_from_email(email)
            username = base_username
            suffix = 1

            # Ensure username is unique
            while True:
                stmt = select(User).where(func.lower(User.username) == username.lower())
                result = await session.execute(stmt)
                if result.scalar_one_or_none() is None:
                    break
                username = f"{base_username}_{suffix}"
                suffix += 1
                if suffix > 100:
                    typer.echo(
                        typer.style(
                            "Error: Could not generate unique username.",
                            fg=typer.colors.RED,
                        )
                    )
                    raise typer.Exit(code=1)

            # Create user
            user = User(
                uid=generate_uid(),
                email=email,
                username=username,
                display_name=name,
                status=UserStatus.ACTIVE.value,
                email_verified_at=datetime.now(timezone.utc),
                is_admin=True,
            )
            session.add(user)
            await session.flush()

            # Create email authentication
            auth = UserAuthentication(
                user_id=user.id,
                provider_type=AuthProviderType.EMAIL.value,
                provider_user_id=email,
                password_hash=hash_password(password),
                is_primary=True,
            )
            session.add(auth)

            # Create admin profile
            admin_profile = UserAdminProfile(
                user_id=user.id,
                role=AdminRole.SUPER_ADMIN.value,
                permissions={},  # Super admin has all permissions implicitly
                granted_at=datetime.now(timezone.utc),
                # granted_by_user_id is None for self-created super admin
            )
            session.add(admin_profile)

            await session.flush()

            typer.echo(
                typer.style(
                    "Super admin created successfully!",
                    fg=typer.colors.GREEN,
                    bold=True,
                )
            )
            typer.echo(f"  UID:      {user.uid}")
            typer.echo(f"  Email:    {email}")
            typer.echo(f"  Username: {username}")
            typer.echo(f"  Name:     {name}")


@init_app.command("admin")
def init_admin(
    email: str = typer.Option(
        ...,
        "--email",
        "-e",
        help="Admin email address",
        prompt="Admin email",
    ),
    password: str = typer.Option(
        ...,
        "--password",
        "-p",
        help="Admin password (min 8 chars, must include upper, lower, digit)",
        prompt="Admin password",
        hide_input=True,
        confirmation_prompt=True,
    ),
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="Admin display name",
        prompt="Admin display name",
    ),
) -> None:
    """
    Initialize a super admin account.

    Creates a new super admin user with the specified email, password, and name.
    The username is automatically generated from the email address.

    Example:
        tabapi init admin --email admin@example.com --name "Admin User"
    """
    # Import password validation from existing schemas (following best practices)
    from tabapi.app.modules.auth.schemas import validate_password_strength

    # Validate email format using Pydantic
    if not validate_email_format(email):
        typer.echo(
            typer.style(
                "Error: Invalid email format.",
                fg=typer.colors.RED,
            )
        )
        raise typer.Exit(code=1)

    # Validate password using existing validation logic
    try:
        validate_password_strength(password)
    except ValueError as e:
        typer.echo(
            typer.style(
                f"Error: {e}",
                fg=typer.colors.RED,
            )
        )
        raise typer.Exit(code=1)

    # Validate name
    if not name or len(name.strip()) == 0:
        typer.echo(
            typer.style(
                "Error: Name cannot be empty.",
                fg=typer.colors.RED,
            )
        )
        raise typer.Exit(code=1)

    if len(name) > 100:
        typer.echo(
            typer.style(
                "Error: Name must be at most 100 characters.",
                fg=typer.colors.RED,
            )
        )
        raise typer.Exit(code=1)

    typer.echo(f"Creating super admin account for: {email}")

    # Bridge async and sync using asyncio.run()
    try:
        asyncio.run(create_super_admin(email, password, name.strip()))
    except Exception as e:
        if not isinstance(e, typer.Exit):
            typer.echo(
                typer.style(
                    f"Error: Failed to create admin - {e}",
                    fg=typer.colors.RED,
                )
            )
            raise typer.Exit(code=1)
        raise


if __name__ == "__main__":
    app()
