from rest_framework.pagination import PageNumberPagination

from api import constants


class ChatsPagination(PageNumberPagination):
    page_size = constants.CHATS_PAGE


class MessagePagination(PageNumberPagination):
    page_size = constants.MESSAGES_PAGE


class UsersPagination(PageNumberPagination):
    page_size = constants.USERS_PAGE
