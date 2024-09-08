from sqlalchemy import create_engine
from sqlalchemy import Column, String, SmallInteger, Integer, Float, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, DeclarativeBase, relationship
from pydantic import BaseModel

engine = create_engine('sqlite:///db.db', echo=True)
SessionLocal = sessionmaker(bind=engine)


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Base(DeclarativeBase):
    pass


class Buyer(Base):
    __tablename__ = 'buyer'
    __table_args__ = {'keep_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(length=30))
    password = Column(String(length=30))
    balance = Column(Float(decimal_return_scale=2), default=0)
    age = Column(SmallInteger())
    buyers_game = relationship('Game', secondary='buyer_game', back_populates='games_buyer')

    def __str__(self):
        return self.name


class BuyerModel(BaseModel):
    username: str
    password: str
    balance: float = 0
    age: int

    def __str__(self):
        return self.username


class BuyerForm(BaseModel):
    username: str
    password: str
    repeat_password: str
    age: int


class Game(Base):
    __tablename__ = 'game'
    __table_args__ = {'keep_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(length=30))
    cost = Column(Float(decimal_return_scale=2), default=0)
    size = Column(Float(decimal_return_scale=2))
    description = Column(String())
    age_limited = Column(Boolean(), default=False)
    games_buyer = relationship('Buyer', secondary='buyer_game', back_populates='buyers_game')

    def __str__(self):
        return self.title+'\t|\t'+str(self.cost)


class GameModel(BaseModel):
    title: str
    cost: float
    size: float
    description: str
    age_limited: bool

    def __str__(self):
        return self.title+'\t|\t'+str(self.cost)


class BuyerGame(Base):
    __tablename__ = 'buyer_game'

    id = Column(Integer, primary_key=True)
    buyer_id = Column(Integer, ForeignKey('buyer.id'))
    game_id = Column(Integer, ForeignKey('game.id'))

