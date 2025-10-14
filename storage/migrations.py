"""
Migrations: Database migration management for ElixirMind.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from alembic import command
from alembic.config import Config
from alembic.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext
import sqlalchemy as sa
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

class MigrationManager:
    """
    Manages database schema migrations using Alembic.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Migration settings
        self.migrations_dir = self.config.get('migrations_dir', 'storage/migrations')
        self.db_url = self.config.get('db_url', 'sqlite:///data/elixir_mind.db')
        self.alembic_config_path = self.config.get('alembic_config', 'alembic.ini')

        # Ensure migrations directory exists
        os.makedirs(self.migrations_dir, exist_ok=True)

        logger.info("Migration Manager initialized")

    def initialize_alembic(self):
        """Initialize Alembic migration environment."""
        try:
            # Create alembic configuration
            alembic_cfg = Config(self.alembic_config_path)

            # Set database URL
            alembic_cfg.set_main_option('sqlalchemy.url', self.db_url)

            # Set script location
            script_location = os.path.join(os.path.dirname(__file__), 'migrations')
            alembic_cfg.set_main_option('script_location', script_location)

            # Initialize migrations directory if it doesn't exist
            if not os.path.exists(os.path.join(script_location, 'versions')):
                command.init(alembic_cfg, script_location)

            logger.info("Alembic initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Alembic: {e}")
            raise

    def create_migration(self, message: str, autogenerate: bool = True) -> str:
        """
        Create a new migration.

        Args:
            message: Migration message
            autogenerate: Whether to autogenerate changes

        Returns:
            Migration revision ID
        """
        try:
            alembic_cfg = Config(self.alembic_config_path)
            alembic_cfg.set_main_option('sqlalchemy.url', self.db_url)

            if autogenerate:
                command.revision(alembic_cfg, message=message, autogenerate=True)
            else:
                command.revision(alembic_cfg, message=message)

            logger.info(f"Created migration: {message}")
            return "revision_created"  # Would normally return revision ID

        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            raise

    def upgrade_database(self, revision: str = 'head'):
        """
        Upgrade database to specified revision.

        Args:
            revision: Target revision ('head' for latest)
        """
        try:
            alembic_cfg = Config(self.alembic_config_path)
            alembic_cfg.set_main_option('sqlalchemy.url', self.db_url)

            command.upgrade(alembic_cfg, revision)
            logger.info(f"Database upgraded to revision: {revision}")

        except Exception as e:
            logger.error(f"Failed to upgrade database: {e}")
            raise

    def downgrade_database(self, revision: str):
        """
        Downgrade database to specified revision.

        Args:
            revision: Target revision
        """
        try:
            alembic_cfg = Config(self.alembic_config_path)
            alembic_cfg.set_main_option('sqlalchemy.url', self.db_url)

            command.downgrade(alembic_cfg, revision)
            logger.info(f"Database downgraded to revision: {revision}")

        except Exception as e:
            logger.error(f"Failed to downgrade database: {e}")
            raise

    def get_current_revision(self) -> Optional[str]:
        """
        Get current database revision.

        Returns:
            Current revision ID or None
        """
        try:
            alembic_cfg = Config(self.alembic_config_path)
            alembic_cfg.set_main_option('sqlalchemy.url', self.db_url)

            script = ScriptDirectory.from_config(alembic_cfg)

            with alembic_cfg.attributes['configure_logger'](False):
                engine = create_engine(self.db_url)
                with engine.connect() as conn:
                    context = MigrationContext.configure(conn)
                    current_rev = context.get_current_revision()

            return current_rev

        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None

    def get_migration_history(self) -> List[Dict]:
        """
        Get migration history.

        Returns:
            List of migration records
        """
        try:
            alembic_cfg = Config(self.alembic_config_path)
            script = ScriptDirectory.from_config(alembic_cfg)

            migrations = []
            for rev in script.walk_revisions():
                migrations.append({
                    'revision': rev.revision,
                    'down_revision': rev.down_revision,
                    'message': rev.doc,
                    'date': getattr(rev, 'date', None)
                })

            return migrations

        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []

    def check_migration_status(self) -> Dict:
        """
        Check migration status and identify any issues.

        Returns:
            Dict with migration status information
        """
        status = {
            'current_revision': self.get_current_revision(),
            'head_revision': None,
            'needs_upgrade': False,
            'issues': []
        }

        try:
            alembic_cfg = Config(self.alembic_config_path)
            script = ScriptDirectory.from_config(alembic_cfg)

            # Get head revision
            head_rev = script.get_current_head()
            status['head_revision'] = head_rev

            # Check if upgrade needed
            current_rev = status['current_revision']
            if current_rev != head_rev:
                status['needs_upgrade'] = True

            # Check for missing migrations
            with create_engine(self.db_url).connect() as conn:
                context = MigrationContext.configure(conn)
                current_heads = context.get_current_heads()

                if len(current_heads) > 1:
                    status['issues'].append("Multiple heads detected")
                elif len(current_heads) == 0:
                    status['issues'].append("No migrations applied")

        except Exception as e:
            status['issues'].append(f"Error checking status: {e}")

        return status

class SimpleMigrationManager:
    """
    Simple migration manager for basic schema changes without Alembic.
    Useful for SQLite databases or simple deployments.
    """

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.applied_migrations = set()

        # Migration registry
        self.migrations = {
            '001_initial_schema': self._migration_001_initial_schema,
            '002_add_performance_indexes': self._migration_002_add_performance_indexes,
            '003_add_training_tables': self._migration_003_add_training_tables,
            '004_add_game_state_tracking': self._migration_004_add_game_state_tracking
        }

    def apply_pending_migrations(self):
        """Apply all pending migrations."""
        engine = create_engine(self.db_url)

        # Create migrations table if it doesn't exist
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    migration_id TEXT PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()

            # Get applied migrations
            result = conn.execute(text("SELECT migration_id FROM schema_migrations"))
            self.applied_migrations = {row[0] for row in result}

        # Apply pending migrations in order
        for migration_id in sorted(self.migrations.keys()):
            if migration_id not in self.applied_migrations:
                logger.info(f"Applying migration: {migration_id}")
                try:
                    self.migrations[migration_id](engine)
                    self._mark_migration_applied(engine, migration_id)
                    logger.info(f"Successfully applied migration: {migration_id}")
                except Exception as e:
                    logger.error(f"Failed to apply migration {migration_id}: {e}")
                    raise

    def _mark_migration_applied(self, engine, migration_id: str):
        """Mark a migration as applied."""
        with engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO schema_migrations (migration_id) VALUES (?)"
            ), (migration_id,))
            conn.commit()

    def _migration_001_initial_schema(self, engine):
        """Initial schema creation."""
        # This would create all initial tables
        # For brevity, just showing the pattern
        with engine.connect() as conn:
            # Create tables here
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY,
                    match_id TEXT UNIQUE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration REAL,
                    result TEXT,
                    trophy_change INTEGER,
                    deck_used TEXT,
                    strategy_used TEXT,
                    confidence_score REAL
                )
            """))
            conn.commit()

    def _migration_002_add_performance_indexes(self, engine):
        """Add performance indexes."""
        with engine.connect() as conn:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_match_timestamp ON matches(timestamp)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_match_result ON matches(result)"))
            conn.commit()

    def _migration_003_add_training_tables(self, engine):
        """Add training session tables."""
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS training_sessions (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT UNIQUE,
                    algorithm TEXT,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT
                )
            """))
            conn.commit()

    def _migration_004_add_game_state_tracking(self, engine):
        """Add game state tracking."""
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS game_states (
                    id INTEGER PRIMARY KEY,
                    match_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    game_time REAL,
                    player_towers TEXT,
                    opponent_towers TEXT
                )
            """))
            conn.commit()
