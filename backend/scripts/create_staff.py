
from getpass import getpass

from sqlmodel import Session, select

from database import engine
from app.models.user import User
from app.auth.password import hash_password


def create_staff():
    print("\n=== CampusFix Staff Account Setup ===\n")

    name = input("Staff name: ").strip()
    email = input("Staff email: ").strip().lower()

    if len(name) < 2:
        print("Error: Name must contain at least 2 characters.")
        return

    if "@" not in email or len(email) > 255:
        print("Error: Please enter a valid email address.")
        return

    password = getpass("Staff password: ")
    confirm_password = getpass("Confirm password: ")

    if len(password) < 8 or len(password) > 128:
        print("Error: Password must be between 8 and 128 characters.")
        return

    if password != confirm_password:
        print("Error: Passwords do not match.")
        return

    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        existing_user = session.exec(statement).first()

        if existing_user:
            print("\nError: An account with this email already exists.")
            return

        staff = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="STAFF",
        )

        session.add(staff)
        session.commit()

        print("\nStaff account created successfully!")
        print(f"Staff email: {email}")
        print("Role: STAFF")


if __name__ == "__main__":
    create_staff()
