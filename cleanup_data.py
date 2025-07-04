#!/usr/bin/env python3
"""
Script to clean up all test data from the Manushya.ai backend.
This script bypasses the API and directly accesses the database.
"""

import asyncio
import uuid
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.db.database import AsyncSessionLocal
from manushya.db.models import Identity, Memory, Policy, AuditLog
from manushya.core.policy_engine import create_default_policies


async def cleanup_all_data():
    """Clean up all test data from the database."""
    async with AsyncSessionLocal() as db:
        print("🔍 Checking existing data...")
        
        # Count existing data
        identities_count = len((await db.execute(select(Identity))).scalars().all())
        memories_count = len((await db.execute(select(Memory))).scalars().all())
        policies_count = len((await db.execute(select(Policy))).scalars().all())
        audit_logs_count = len((await db.execute(select(AuditLog))).scalars().all())
        
        print(f"📊 Found {identities_count} identities, {memories_count} memories, {policies_count} policies, {audit_logs_count} audit logs")
        
        if identities_count == 0 and memories_count == 0 and policies_count == 0 and audit_logs_count == 0:
            print("✅ No data to clean up!")
            return
        
        print("🗑️  Starting cleanup...")
        
        # Delete all data in the correct order (respecting foreign key constraints)
        print("  - Deleting audit logs...")
        await db.execute(delete(AuditLog))
        
        print("  - Deleting memories...")
        await db.execute(delete(Memory))
        
        print("  - Deleting policies...")
        await db.execute(delete(Policy))
        
        print("  - Deleting identities...")
        await db.execute(delete(Identity))
        
        # Commit the changes
        await db.commit()
        
        print("✅ All test data has been deleted!")
        
        # Verify cleanup
        identities_count = len((await db.execute(select(Identity))).scalars().all())
        memories_count = len((await db.execute(select(Memory))).scalars().all())
        policies_count = len((await db.execute(select(Policy))).scalars().all())
        audit_logs_count = len((await db.execute(select(AuditLog))).scalars().all())
        
        print(f"📊 Verification: {identities_count} identities, {memories_count} memories, {policies_count} policies, {audit_logs_count} audit logs remaining")


async def create_admin_policies():
    """Create admin policies to enable API access."""
    async with AsyncSessionLocal() as db:
        print("🔧 Creating admin policies...")
        await create_default_policies(db)
        print("✅ Admin policies created!")


async def main():
    """Main function to run the cleanup."""
    print("🚀 Starting Manushya.ai data cleanup...")
    
    try:
        # First create admin policies
        await create_admin_policies()
        
        # Then clean up all data
        await cleanup_all_data()
        
        print("🎉 Cleanup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 