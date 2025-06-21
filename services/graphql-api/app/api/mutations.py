"""
GraphQL mutations for the API
"""
import graphene
from datetime import datetime
from app.api.types import (
    UserType, VoiceSessionType, VoiceInteractionType,
    UserInput, UserUpdateInput, VoiceSessionInput, VoiceSessionUpdateInput, VoiceInteractionInput
)


class CreateUser(graphene.Mutation):
    """
    Mutation to create a new user
    """
    class Arguments:
        input = UserInput(required=True)
    
    user = graphene.Field(UserType)
    
    @staticmethod
    def mutate(root, info, input):
        from app.services.user_service import create_user
        user = create_user(
            username=input.username,
            email=input.email,
            password=input.password,
            is_active=input.is_active,
            is_superuser=input.is_superuser
        )
        return CreateUser(user=user)


class UpdateUser(graphene.Mutation):
    """
    Mutation to update an existing user
    """
    class Arguments:
        id = graphene.Int(required=True)
        input = UserUpdateInput(required=True)
    
    user = graphene.Field(UserType)
    
    @staticmethod
    def mutate(root, info, id, input):
        from app.services.user_service import update_user
        user = update_user(
            user_id=id,
            username=input.username,
            email=input.email,
            password=input.password,
            is_active=input.is_active,
            is_superuser=input.is_superuser
        )
        return UpdateUser(user=user)


class DeleteUser(graphene.Mutation):
    """
    Mutation to delete a user
    """
    class Arguments:
        id = graphene.Int(required=True)
    
    success = graphene.Boolean()
    
    @staticmethod
    def mutate(root, info, id):
        from app.services.user_service import delete_user
        success = delete_user(user_id=id)
        return DeleteUser(success=success)


class CreateVoiceSession(graphene.Mutation):
    """
    Mutation to create a new voice session
    """
    class Arguments:
        input = VoiceSessionInput(required=True)
    
    voice_session = graphene.Field(VoiceSessionType)
    
    @staticmethod
    def mutate(root, info, input):
        from app.services.voice_service import create_voice_session
        voice_session = create_voice_session(
            user_id=input.user_id,
            language=input.language,
            metadata=input.metadata
        )
        return CreateVoiceSession(voice_session=voice_session)


class UpdateVoiceSession(graphene.Mutation):
    """
    Mutation to update an existing voice session
    """
    class Arguments:
        id = graphene.Int(required=True)
        input = VoiceSessionUpdateInput(required=True)
    
    voice_session = graphene.Field(VoiceSessionType)
    
    @staticmethod
    def mutate(root, info, id, input):
        from app.services.voice_service import update_voice_session
        voice_session = update_voice_session(
            session_id=id,
            status=input.status,
            language=input.language,
            metadata=input.metadata
        )
        return UpdateVoiceSession(voice_session=voice_session)


class EndVoiceSession(graphene.Mutation):
    """
    Mutation to end a voice session
    """
    class Arguments:
        id = graphene.Int(required=True)
    
    voice_session = graphene.Field(VoiceSessionType)
    
    @staticmethod
    def mutate(root, info, id):
        from app.services.voice_service import end_voice_session
        voice_session = end_voice_session(session_id=id)
        return EndVoiceSession(voice_session=voice_session)


class CreateVoiceInteraction(graphene.Mutation):
    """
    Mutation to create a new voice interaction
    """
    class Arguments:
        input = VoiceInteractionInput(required=True)
    
    voice_interaction = graphene.Field(VoiceInteractionType)
    
    @staticmethod
    def mutate(root, info, input):
        from app.services.voice_service import create_voice_interaction
        voice_interaction = create_voice_interaction(
            session_id=input.session_id,
            user_input=input.user_input,
            system_response=input.system_response,
            audio_file_path=input.audio_file_path,
            confidence_score=input.confidence_score,
            intent=input.intent,
            entities=input.entities
        )
        return CreateVoiceInteraction(voice_interaction=voice_interaction)