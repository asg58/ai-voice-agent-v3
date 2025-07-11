from graphene import ObjectType, String, Schema

class Query(ObjectType):
    hello = String(name=String(default_value="world"))

    def resolve_hello(root, info, name):
        return f"Hello {name}!"

schema = Schema(query=Query)
