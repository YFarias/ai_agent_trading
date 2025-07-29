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

# GraphQL
app.include_router(graphql_app, prefix="/graphql")
