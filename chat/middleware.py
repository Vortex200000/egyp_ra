from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()

@database_sync_to_async
def get_user(token_key):
    try:
        UntypedToken(token_key)
        user = User.objects.get(id=UntypedToken(token_key)['user_id'])
        return user
    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token")
        if token:
            scope["user"] = await get_user(token[0])
        else:
            scope["user"] = AnonymousUser()
        return await super().__call__(scope, receive, send)