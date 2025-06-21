"""
GraphQL types for the API
"""
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType
from app.models.user import User
from app.models.voice_session import VoiceSession, VoiceInteraction


class UserType(SQLAlchemyObjectType):
    """
    GraphQL type for User model
    """
    class Meta:
        model = User
        exclude = ("hashed_password",)


class VoiceSessionType(SQLAlchemyObjectType):
    """
    GraphQL type for VoiceSession model
    """
    class Meta:
        model = VoiceSession


class VoiceInteractionType(SQLAlchemyObjectType):
    """
    GraphQL type for VoiceInteraction model
    """
    class Meta:
        model = VoiceInteraction


class UserInput(graphene.InputObjectType):
    """
    Input type for User mutations
    """
    username = graphene.String(required=True)
    email = graphene.String(required=True)
    password = graphene.String(required=True)
    is_active = graphene.Boolean()
    is_superuser = graphene.Boolean()


class UserUpdateInput(graphene.InputObjectType):
    """
    Input type for User update mutations
    """
    username = graphene.String()
    email = graphene.String()
    password = graphene.String()
    is_active = graphene.Boolean()
    is_superuser = graphene.Boolean()


class VoiceSessionInput(graphene.InputObjectType):
    """
    Input type for VoiceSession mutations
    """
    user_id = graphene.Int(required=True)
    language = graphene.String(required=True)
    metadata = graphene.JSONString()


class VoiceSessionUpdateInput(graphene.InputObjectType):
    """
    Input type for VoiceSession update mutations
    """
    status = graphene.String()
    language = graphene.String()
    metadata = graphene.JSONString()


class VoiceInteractionInput(graphene.InputObjectType):
    """
    Input type for VoiceInteraction mutations
    """
    session_id = graphene.Int(required=True)
    user_input = graphene.String()
    system_response = graphene.String()
    audio_file_path = graphene.String()
    confidence_score = graphene.Int()
    intent = graphene.String()
    entities = graphene.JSONString()