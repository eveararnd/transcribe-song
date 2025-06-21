#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Initialize database tables for Music Analyzer
"""
import asyncio
import os
from src.models.music_analyzer_models import DatabaseManager, Base
from src.config.music_analyzer_config import DATABASE_URL

async def init_database():
    """Initialize database tables"""
    print("Initializing database...")
    
    # Create database manager
    db_manager = DatabaseManager(DATABASE_URL)
    await db_manager.initialize()
    
    # Create tables
    await db_manager.create_tables()
    
    print("Database tables created successfully!")
    
    # Close connection
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(init_database())