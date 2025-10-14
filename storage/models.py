"""
Models: ORM models using SQLAlchemy for ElixirMind data structures.
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class Player(Base):
    """Player profile and statistics."""
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    player_tag = Column(String(20), unique=True, index=True)
    name = Column(String(100))
    level = Column(Integer)
    trophies = Column(Integer)
    best_trophies = Column(Integer)
    experience = Column(Integer)
    clan_tag = Column(String(20))
    clan_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    meta_data = Column(JSON)

    # Relationships
    matches = relationship("Match", back_populates="player")
    decks = relationship("PlayerDeck", back_populates="player")

class Deck(Base):
    """Deck templates and configurations."""
    __tablename__ = "decks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    cards = Column(JSON)  # List of card IDs and counts
    avg_elixir = Column(Float)
    deck_type = Column(String(50))  # ladder, challenge, etc.
    archetype = Column(String(50))  # control, beatdown, etc.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_used = Column(DateTime)
    win_rate = Column(Float, default=0.0)
    total_games = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    avg_game_duration = Column(Float)  # seconds
    meta_data = Column(JSON)

    # Relationships
    matches = relationship("Match", back_populates="deck")
    player_decks = relationship("PlayerDeck", back_populates="deck")

class PlayerDeck(Base):
    """Player-deck associations with performance data."""
    __tablename__ = "player_decks"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    deck_id = Column(Integer, ForeignKey("decks.id"))
    is_active = Column(Boolean, default=False)
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    best_trophy_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_used = Column(DateTime)

    # Relationships
    player = relationship("Player", back_populates="decks")
    deck = relationship("Deck", back_populates="player_decks")

class Match(Base):
    """Match data and results."""
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String(50), unique=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    deck_id = Column(Integer, ForeignKey("decks.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    duration = Column(Float)  # seconds
    result = Column(String(20))  # win, loss, draw
    trophy_change = Column(Integer, default=0)
    crowns = Column(Integer, default=0)  # crowns earned
    opponent_crowns = Column(Integer, default=0)
    opponent_name = Column(String(100))
    opponent_trophies = Column(Integer)
    opponent_deck = Column(JSON)  # detected opponent cards
    opponent_clan = Column(String(100))
    battle_type = Column(String(50))  # ladder, challenge, clan_war, etc.
    arena = Column(String(50))
    strategy_used = Column(String(50))
    confidence_score = Column(Float)
    ai_decisions = Column(Integer, default=0)  # number of AI decisions made
    manual_interventions = Column(Integer, default=0)
    meta_data = Column(JSON)

    # Relationships
    player = relationship("Player", back_populates="matches")
    deck = relationship("Deck", back_populates="matches")
    actions = relationship("MatchAction", back_populates="match", cascade="all, delete-orphan")
    stats = relationship("MatchStats", back_populates="match", cascade="all, delete-orphan")

class MatchAction(Base):
    """Individual actions taken during a match."""
    __tablename__ = "match_actions"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    action_type = Column(String(50))  # play_card, attack, spell, etc.
    card_id = Column(String(50))  # which card was played
    position = Column(JSON)  # x, y coordinates or target info
    elixir_cost = Column(Float)
    confidence = Column(Float)  # AI confidence in this action
    success = Column(Boolean)  # whether action was successful
    damage_dealt = Column(Float)
    damage_taken = Column(Float)
    crowns_earned = Column(Integer, default=0)
    meta_data = Column(JSON)

    match = relationship("Match", back_populates="actions")

class MatchStats(Base):
    """Detailed statistics for match performance."""
    __tablename__ = "match_stats"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    stat_type = Column(String(50))  # damage_dealt, cards_played, etc.
    value = Column(Float)
    category = Column(String(50))  # offensive, defensive, economic
    meta_data = Column(JSON)

    match = relationship("Match", back_populates="stats")

class Card(Base):
    """Card definitions and statistics."""
    __tablename__ = "cards"

    id = Column(String(50), primary_key=True)  # card ID/key
    name = Column(String(100), index=True)
    rarity = Column(String(20))  # common, rare, epic, legendary
    elixir_cost = Column(Integer)
    card_type = Column(String(50))  # troop, spell, building
    arena = Column(String(50))
    description = Column(Text)
    hitpoints = Column(Integer)
    damage = Column(Float)
    damage_per_second = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    meta_data = Column(JSON)

    # Relationships
    performances = relationship("CardPerformance", back_populates="card", cascade="all, delete-orphan")

class CardPerformance(Base):
    """Performance statistics for individual cards."""
    __tablename__ = "card_performances"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(String(50), ForeignKey("cards.id"))
    deck_id = Column(Integer, ForeignKey("decks.id"))
    total_plays = Column(Integer, default=0)
    successful_plays = Column(Integer, default=0)
    avg_damage_dealt = Column(Float, default=0.0)
    avg_damage_taken = Column(Float, default=0.0)
    win_rate_when_played = Column(Float, default=0.0)
    avg_position_played = Column(Float)  # average elixir at time of play
    last_used = Column(DateTime)
    meta_data = Column(JSON)

    card = relationship("Card", back_populates="performances")

class PerformanceMetrics(Base):
    """System performance monitoring data."""
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    metric_type = Column(String(50))  # cpu, memory, fps, latency
    value = Column(Float)
    component = Column(String(50))  # vision, strategy, actions
    session_id = Column(String(50))
    meta_data = Column(JSON)

class Alert(Base):
    """System alerts and notifications."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    alert_type = Column(String(50))  # performance, error, security
    severity = Column(String(20))  # info, warning, error, critical
    message = Column(Text)
    component = Column(String(50))
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    meta_data = Column(JSON)

class SystemConfig(Base):
    """System configuration storage."""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True)
    value = Column(JSON)
    value_type = Column(String(20))  # string, int, float, bool, json
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_by = Column(String(50))  # component that updated
    description = Column(Text)
    is_sensitive = Column(Boolean, default=False)

class TrainingSession(Base):
    """AI training session data."""
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), unique=True, index=True)
    algorithm = Column(String(50))  # ppo, dqn, etc.
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime)
    total_steps = Column(Integer, default=0)
    total_episodes = Column(Integer, default=0)
    avg_reward = Column(Float)
    best_reward = Column(Float)
    win_rate = Column(Float)
    config = Column(JSON)  # training configuration
    status = Column(String(20))  # running, completed, failed
    meta_data = Column(JSON)

class GameState(Base):
    """Game state snapshots for analysis."""
    __tablename__ = "game_states"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    game_time = Column(Float)  # seconds into the match
    player_towers = Column(JSON)  # tower health states
    opponent_towers = Column(JSON)  # opponent tower health states
    player_elixir = Column(Float)
    opponent_elixir = Column(Float)
    player_cards = Column(JSON)  # cards in hand
    opponent_cards = Column(JSON)  # detected opponent cards
    units_on_field = Column(JSON)  # all units and their positions
    meta_data = Column(JSON)

# Create indexes for better query performance
Index('idx_match_timestamp', Match.timestamp)
Index('idx_match_result', Match.result)
Index('idx_match_player', Match.player_id)
Index('idx_match_deck', Match.deck_id)
Index('idx_performance_timestamp', PerformanceMetrics.timestamp)
Index('idx_performance_type', PerformanceMetrics.metric_type)
Index('idx_alert_timestamp', Alert.timestamp)
Index('idx_alert_type', Alert.alert_type)
Index('idx_training_session_status', TrainingSession.status)
