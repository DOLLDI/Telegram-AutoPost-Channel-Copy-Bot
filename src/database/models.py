from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime # type: ignore
from sqlalchemy.ext.declarative import declarative_base # type: ignore
from sqlalchemy.orm import sessionmaker # type: ignore
from datetime import datetime
import os

Base = declarative_base()


class BotSettings(Base):
    """Bot configuration settings"""
    __tablename__ = 'bot_settings'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, unique=True, nullable=False)
    source_channel_id = Column(Integer, nullable=False)
    target_channel_id = Column(Integer, nullable=False)
    auto_posting_enabled = Column(Boolean, default=False)
    custom_link = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PostHistory(Base):
    """History of reposted messages"""
    __tablename__ = 'post_history'
    
    id = Column(Integer, primary_key=True)
    original_message_id = Column(Integer, nullable=False)
    original_channel_id = Column(Integer, nullable=False)
    reposted_message_id = Column(Integer, nullable=False)
    target_channel_id = Column(Integer, nullable=False)
    original_link = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class PendingPost(Base):
    """Posts waiting for admin approval"""
    __tablename__ = 'pending_posts'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, nullable=False, unique=True)
    channel_id = Column(Integer, nullable=False)
    content = Column(Text)
    has_media = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='pending')


class DatabaseManager:
    """Database manager class"""
    
    def __init__(self, db_path='data/bot.db'):
        self.db_path = db_path
        
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
        
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close the database connection"""
        self.engine.dispose()


db = None


def init_db(db_path='data/bot.db'):
    """Initialize the database"""
    global db
    db = DatabaseManager(db_path)
    return db


def get_db():
    """Get the global database instance"""
    global db
    if db is None:
        db = DatabaseManager()
    return db
