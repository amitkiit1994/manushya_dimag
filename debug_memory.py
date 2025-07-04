#!/usr/bin/env python3

import asyncio

from sqlalchemy import select

from manushya.db.database import AsyncSessionLocal
from manushya.db.models import Identity, Memory


async def debug_memory():
    """Debug function to check memory and identity data."""
    async with AsyncSessionLocal() as session:
        # Check memories
        result = await session.execute(select(Memory))
        memories = result.scalars().all()
        print(f"Total memories in DB: {len(memories)}")

        for memory in memories:
            print(f"Memory ID: {memory.id}")
            print(f"Identity ID: {memory.identity_id}")
            print(f"Text: {memory.text[:50]}...")
            print(f"Type: {memory.type}")
            print(f"Is deleted: {memory.is_deleted}")
            print("---")

        # Check identities
        result = await session.execute(select(Identity))
        identities = result.scalars().all()
        print(f"Total identities in DB: {len(identities)}")

        for identity in identities:
            print(f"Identity ID: {identity.id}")
            print(f"External ID: {identity.external_id}")
            print(f"Role: {identity.role}")
            print(f"Is active: {identity.is_active}")
            print("---")


if __name__ == "__main__":
    asyncio.run(debug_memory())
