"""
Seed script to add initial users to the database.
Run this after starting the backend.
"""

import asyncio
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, '/app')

from app.models.db_models import Base, User
from app.utils.auth_utils import encrypt_password
from app.config import get_settings


async def seed_users():
    """Seed initial users into database."""
    settings = get_settings()
    
    # Create engine
    engine = create_async_engine(settings.database_url, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if seed user already exists
            query = select(User).where(User.username == "sumitsri051@gmail.com")
            result = await session.execute(query)
            existing = result.scalar_one_or_none()
            
            if existing:
                print("✓ Seed user already exists: sumitsri051@gmail.com")
                return
            
            # Create seed user
            encrypted_pwd = encrypt_password("Cgi@123")
            seed_user = User(
                email="sumitsri051@gmail.com",
                username="sumitsri051@gmail.com",
                encrypted_password=encrypted_pwd,
                is_active=True
            )
            
            session.add(seed_user)
            await session.commit()
            
            print("✓ Seed user created successfully!")
            print(f"  Email: sumitsri051@gmail.com")
            print(f"  Username: sumitsri051@gmail.com")
            print(f"  Password: Cgi@123")
            
        except Exception as e:
            print(f"✗ Error seeding users: {e}")
            await session.rollback()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_users())
