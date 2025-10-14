"""
Database: SQLite/PostgreSQL database management for ElixirMind.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.pool import StaticPool
import datetime

logger = logging.getLogger(__name__)

Base = declarative_base()

class DatabaseManager:
    """
    Manages database connections and operations for ElixirMind.
    Supports both SQLite (development) and PostgreSQL (production).
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Database settings
        self.db_type = self.config.get('db_type', 'sqlite')  # sqlite or postgresql
        self.db_path = self.config.get('db_path', 'data/elixir_mind.db')
        self.db_url = self.config.get('db_url', '')  # For PostgreSQL

        # Connection settings
        self.pool_size = self.config.get('pool_size', 5)
        self.max_overflow = self.config.get('max_overflow', 10)
        self.pool_timeout = self.config.get('pool_timeout', 30)

        # Engine and session
        self.engine = None
        self.SessionLocal = None

        # Initialize database
        self._initialize_database()

        logger.info(f"Database Manager initialized with {self.db_type}")

    def _initialize_database(self):
        """Initialize database connection and create tables."""
        try:
            if self.db_type == 'sqlite':
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

                # SQLite connection string
                database_url = f"sqlite:///{self.db_path}"

                # Create engine with SQLite-specific settings
                self.engine = create_engine(
                    database_url,
                    connect_args={'check_same_thread': False},
                    poolclass=StaticPool,
                    echo=self.config.get('echo_sql', False)
                )

            elif self.db_type == 'postgresql':
                # PostgreSQL connection string
                if not self.db_url:
                    raise ValueError("PostgreSQL URL not provided")

                self.engine = create_engine(
                    self.db_url,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_timeout=self.pool_timeout,
                    echo=self.config.get('echo_sql', False)
                )

            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")

            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

            # Create all tables
            Base.metadata.create_all(bind=self.engine)

            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def close_session(self, session: Session):
        """Close a database session."""
        session.close()

    def health_check(self) -> bool:
        """Check database health."""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def backup_database(self, backup_path: str) -> bool:
        """Backup the database."""
        try:
            if self.db_type == 'sqlite':
                import shutil
                shutil.copy2(self.db_path, backup_path)
                logger.info(f"Database backed up to: {backup_path}")
                return True
            else:
                # For PostgreSQL, use pg_dump or similar
                logger.warning("PostgreSQL backup not implemented")
                return False
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get database statistics."""
        stats = {
            'db_type': self.db_type,
            'healthy': self.health_check()
        }

        try:
            with self.get_session() as session:
                # Get table counts
                for table_name in Base.metadata.tables.keys():
                    try:
                        result = session.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = result.scalar()
                        stats[f'{table_name}_count'] = count
                    except Exception:
                        stats[f'{table_name}_count'] = 'error'

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")

        return stats

    def optimize_database(self):
        """Optimize database performance."""
        try:
            with self.get_session() as session:
                if self.db_type == 'sqlite':
                    # SQLite optimizations
                    session.execute("VACUUM")
                    session.execute("ANALYZE")
                    logger.info("SQLite database optimized")
                elif self.db_type == 'postgresql':
                    # PostgreSQL optimizations
                    session.execute("VACUUM ANALYZE")
                    logger.info("PostgreSQL database optimized")

                session.commit()

        except Exception as e:
            logger.error(f"Database optimization failed: {e}")

# Database Models

class Match(Base):
    """Match data model."""
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String(50), unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    duration = Column(Float)  # seconds
    result = Column(String(20))  # win, loss, draw
    trophy_change = Column(Integer)
    deck_used = Column(JSON)  # deck composition
    opponent_deck = Column(JSON)  # detected opponent deck
    strategy_used = Column(String(50))
    confidence_score = Column(Float)
    meta_data = Column(JSON)  # additional match data

    # Relationships
    actions = relationship("MatchAction", back_populates="match")
    stats = relationship("MatchStats", back_populates="match")

class MatchAction(Base):
    """Individual actions within a match."""
    __tablename__ = "match_actions"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    action_type = Column(String(50))
    position = Column(JSON)  # x, y coordinates
    confidence = Column(Float)
    success = Column(Boolean)
    meta_data = Column(JSON)

    match = relationship("Match", back_populates="actions")

class MatchStats(Base):
    """Detailed statistics for a match."""
    __tablename__ = "match_stats"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    stat_type = Column(String(50))
    value = Column(Float)
    meta_data = Column(JSON)

    match = relationship("Match", back_populates="stats")

class Deck(Base):
    """Deck configurations."""
    __tablename__ = "decks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    cards = Column(JSON)  # card composition
    avg_elixir = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_used = Column(DateTime)
    win_rate = Column(Float)
    total_games = Column(Integer, default=0)
    meta_data = Column(JSON)

class PerformanceMetrics(Base):
    """Performance monitoring data."""
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    metric_type = Column(String(50))
    value = Column(Float)
    component = Column(String(50))
    meta_data = Column(JSON)

class Alert(Base):
    """System alerts and notifications."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    alert_type = Column(String(50))
    severity = Column(String(20))  # info, warning, error, critical
    message = Column(Text)
    component = Column(String(50))
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    meta_data = Column(JSON)

class SystemConfig(Base):
    """System configuration storage."""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True)
    value = Column(JSON)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(Text)
