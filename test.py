import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI()
DATABASE_URL = "postgresql://user:password@localhost:5432/database"
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

    # engine = create_engine(DATABASE_URL)
    # Base = declarative_base() 
    # Session = sessionmaker(bind=engine)
    # session = Session()

    # class Book(Base):
    #     __tablename__ = "books"

    #     id = Column(Integer, primary_key=True)
    #     title = Column(String)
    #     instructor = Column(String)
    #     publish_date = Column(String)

    # Base.metadata.create_all(engine)


class Item(BaseModel):
    name: str
    description: str
    price: float
    tax: float
    
@app.post("/items/")
async def create_item(item: Item):
    cursor.execute(
        "INSERT INTO items (name, description, price, tax) VALUES (%s, %s, %s, %s) RETURNING id",
        (item.name, item.description, item.price, item.tax)
    )
    item_id = cursor.fetchone()[0]
    conn.commit()
    return {"id": item_id}
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    cursor.execute(
        "SELECT name, description, price, tax FROM items WHERE id = %s",
        (item_id,)
    )
    item = cursor.fetchone()
    return {"id": item_id, "name": item[0], "description": item[1], "price": item[2], "tax": item[3]}
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    cursor.execute(
        "UPDATE items SET name = %s, description = %s, price = %s, tax = %s WHERE id = %s",
        (item.name, item.description, item.price, item.tax, item_id)
    )
    conn.commit()
    return {"id": item_id, "name": item.name, "description": item.description, "price": item.price, "tax": item.tax}
@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    cursor.execute(
        "DELETE FROM items WHERE id = %s",
        (item_id,)
    )
    conn.commit()
    return {"id": item_id}
