# backend/app/main.py
from fastapi import FastAPI
import strawberry
from strawberry.fastapi import GraphQLRouter

from uuid import UUID
from datetime import datetime, timezone

# GraphQL
@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello from GraphQL 👋"

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)

# FastAPI
app = FastAPI()

# GraphQL - Admin GUI
app.include_router(graphql_app, prefix="/graphql")


#REST API - Service API
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI 👋"}





