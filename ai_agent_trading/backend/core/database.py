from sqlmodel import create_engine, SQLModel
from core.config import settings

engine = create_engine(settings.get_database_url(), echo=True)

def create_db_and_tables():
    from user.models import User, UserDashboard

    SQLModel.metadata.drop_all(engine) 
    SQLModel.metadata.create_all(engine)
