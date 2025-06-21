"""
GraphQL schema for the API
"""
import graphene
from app.api.types import UserType, VoiceSessionType, VoiceInteractionType
from app.api.mutations import (
    CreateUser, UpdateUser, DeleteUser,
    CreateVoiceSession, UpdateVoiceSession, EndVoiceSession,
    CreateVoiceInteraction
)


class Query(graphene.ObjectType):
    """
    GraphQL Query type
    """
    # User queries
    users = graphene.List(UserType, description="Get all users")
    user = graphene.Field(UserType, id=graphene.Int(required=True), description="Get a user by ID")
    
    # Voice session queries
    voice_sessions = graphene.List(
        VoiceSessionType, 
        user_id=graphene.Int(), 
        status=graphene.String(),
        description="Get all voice sessions, optionally filtered by user ID or status"
    )
    voice_session = graphene.Field(
        VoiceSessionType, 
        id=graphene.Int(), 
        session_id=graphene.String(),
        description="Get a voice session by ID or session ID"
    )
    
    # Voice interaction queries
    voice_interactions = graphene.List(
        VoiceInteractionType,
        session_id=graphene.Int(required=True),
        description="Get all voice interactions for a session"
    )
    
    def resolve_users(self, info):
        from app.services.user_service import get_all_users
        return get_all_users()
    
    def resolve_user(self, info, id):
        from app.services.user_service import get_user_by_id
        return get_user_by_id(id)
    
    def resolve_voice_sessions(self, info, user_id=None, status=None):
        from app.services.voice_service import get_voice_sessions
        return get_voice_sessions(user_id=user_id, status=status)
    
    def resolve_voice_session(self, info, id=None, session_id=None):
        from app.services.voice_service import get_voice_session
        return get_voice_session(id=id, session_id=session_id)
    
    def resolve_voice_interactions(self, info, session_id):
        from app.services.voice_service import get_voice_interactions
        return get_voice_interactions(session_id=session_id)


class Mutation(graphene.ObjectType):
    """
    GraphQL Mutation type
    """
    # User mutations
    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()
    
    # Voice session mutations
    create_voice_session = CreateVoiceSession.Field()
    update_voice_session = UpdateVoiceSession.Field()
    end_voice_session = EndVoiceSession.Field()
    
    # Voice interaction mutations
    create_voice_interaction = CreateVoiceInteraction.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)