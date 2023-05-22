import strawberry
import uvicorn
from fastapi import FastAPI, Depends, Request, WebSocket, BackgroundTasks
from strawberry.types import Info
from strawberry.fastapi import GraphQLRouter
import typing
import json 
import psycopg2
import os

# $ ip addr show docker0 | grep -Po 'inet \K[\d.]+'

# DATABASE_URL = "postgresql://postgres:postgres@host.docker.internal:5433/postgres" 
# DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres" 

try:

    # Establish a connection
    # conn = psycopg2.connect(
    #     host=os.environ['PG_HOST'],
    #     port= os.environ['PG_PORT'],
    #     database=os.environ['PG_DATABASE'],
    #     user=os.environ['PG_USER'],
    #     password=os.environ['PG_PASSWORD']
    # )

    conn = psycopg2.connect(
        host='database',
        port= 5432,
        database='postgres',
        user='postgres',
        password='postgres'
    )

    # conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cursor = conn.cursor()
    print("Connected to the PostgreSQL database")

except (Exception, psycopg2.DatabaseError) as error:
    print("Cannot connect to the PostgreSQL database")
    print(error)  

async def get_books():
     
    try :
        cursor.execute( 
            "CREATE TABLE IF NOT EXISTS books (id SERIAL PRIMARY KEY, title VARCHAR(255), instructor VARCHAR(255), publish_date VARCHAR(255))"
        )
        conn.commit()
        print("Table created successfully")
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        pass

    # get data from postgres database 
    cursor.execute("SELECT * FROM books")
    course_list = cursor.fetchall()
    books = []
    for course in course_list: 
            books.append(Book(id=course[0], title=course[1], instructor=course[2], publish_date=course[3]))
    return books    

@strawberry.type
class Book:
    id: str
    title: str
    instructor: str
    publish_date: str

@strawberry.type
class Query:

    @strawberry.field
    def environment(self, info: Info) -> str:
        list = []
        for key, value in os.environ.items():
            list.append(key + " : " + value)
        return str(list)
        

    all_books: typing.List[Book] = strawberry.field(resolver=get_books)
    
    @strawberry.field
    def book(self, id: str) -> Book: 
        with open("data.json") as courses:
            course_list = json.load(courses)
            print(course_list)
            for course in course_list:
                print("id" , id , course['id'])
                if course['id'] == id:
                    return Book(id=course['id'], title=course['title'], instructor=course['instructor'], publish_date=course['publish_date'])                                
        return Book(id="0", title="No book found", instructor="No book found", publish_date="No book found")

@strawberry.type
class Mutation:

    @strawberry.mutation 
    def add_book(self, title: str, instructor: str, publish_date: str) -> Book:
        # add data to postgres database 
        cursor.execute( 
            "INSERT INTO books (title, instructor, publish_date) VALUES (%s, %s, %s) RETURNING id",
            (title, instructor, publish_date)
        )
        book_id = cursor.fetchone()[0]
        conn.commit()
        return Book(id=book_id, title=title, instructor=instructor, publish_date=publish_date)

    @strawberry.mutation 
    def update_book(self, id: str, title: str, instructor: str, publish_date: str) -> Book:

        # query old data 
        cursor.execute("SELECT * FROM books WHERE id = %s", (id,))
        course_list = cursor.fetchone()
        print(course_list)
        if course_list is None:
            return Book(id="0", title="No book found", instructor="No book found", publish_date="No book found")

        if title == "" or title is None:
            title = course_list[1]
        if instructor == "" or instructor is None:
            instructor = course_list[2] 
        if publish_date == "" or publish_date is None:
            publish_date = course_list[3]

        cursor.execute( 
            "UPDATE books SET title = %s, instructor = %s, publish_date = %s WHERE id = %s",
            (title, instructor, publish_date, id)
        )
        conn.commit()
        return Book(id=id, title=title, instructor=instructor, publish_date=publish_date)

    @strawberry.mutation
    def delete_book(self, id: str) -> Book:
        # query old data 
        cursor.execute("SELECT * FROM books WHERE id = %s", (id,))
        course_list = cursor.fetchone()
        print(course_list)
        if course_list is None:
            return Book(id="0", title="No book found", instructor="No book found", publish_date="No book found")

        cursor.execute("DELETE FROM books WHERE id = %s", (id,))
        conn.commit()
        return Book(id=id, title=course_list[1], instructor=course_list[2], publish_date=course_list[3])

schema = strawberry.Schema(Query, Mutation)


graphql_app = GraphQLRouter(
    schema,
)


app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")

# main function 
if __name__ == "__main__": 
    print(os.environ['PG_HOST'] , os.environ['PG_DATABASE'] , os.environ['PG_USER'] , os.environ['PG_PASSWORD']) 
    uvicorn.run(app, host='0.0.0.0', port=8000)