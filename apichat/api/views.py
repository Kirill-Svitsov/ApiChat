from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api import custom_filters
from api import serializers
from api import pagination
from messenger.models import Chat, Message
from users.models import User


class ChatViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для работы с чатами и сообщениями
    """
    queryset = Chat.objects.select_related(
        'recipient',
        'sender'
    ).prefetch_related('message__author').all()
    pagination_class = pagination.ChatsPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = custom_filters.ChatFilter

    def get_queryset(self):
        """Получение чатов, в которых присутствует Юзер"""
        user = self.request.user
        return self.queryset.filter(
            models.Q(sender=user) | models.Q(recipient=user)
        )

    def get_serializer_class(self):
        """Получение сериализатора в зависимости от запроса"""
        if self.action == ('retrieve', 'list'):
            return serializers.ChatSerializer
        return serializers.ChatCreateSerializer

    def get_object(self):
        """
        Метод получения информации о конкретном чате,
        с проверкой прав доступа к этому чату
        """
        obj = super().get_object()
        user = self.request.user
        if user != obj.sender and user != obj.recipient:
            raise PermissionDenied("Вы не являетесь участником этого чата")
        return obj

    def create(self, request, *args, **kwargs):
        """
        Метод создания чата
        """
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['GET', 'POST'],
        permission_classes=(IsAuthenticated,),
        url_path='messages',
        description='Создание/получение сообщения в чате'
    )
    def handle_messages(self, request, pk):
        """
        Метод получения или отправления сообщений.
        """
        chat = self.get_object()
        # Получение параметров фильтрации из запроса
        text_filter = request.query_params.get('text', None)
        author_filter = request.query_params.get('author', None)
        # Фильтрация сообщений в чате
        messages = Message.objects.filter(chat=chat)
        if text_filter:
            messages = messages.filter(text__icontains=text_filter)
        if author_filter:
            messages = messages.filter(author__username=author_filter)
        if request.method == 'GET':
            # Применение пагинации к отфильтрованным сообщениям
            pagination_messages = pagination.MessagePagination()
            page = pagination_messages.paginate_queryset(messages, request)
            serializer = serializers.MessageSerializer(page, many=True)
            return pagination_messages.get_paginated_response(serializer.data)
        # Если метод запроса - POST
        elif request.method == 'POST':
            # Создание нового сообщения в чате
            serializer = serializers.MessageSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            message = serializer.save(chat=chat, author=request.user)
            return Response(
                serializers.MessageSerializer(message).data,
                status=status.HTTP_201_CREATED
            )

    @action(
        detail=True,
        methods=['GET', 'PUT', 'PATCH', 'DELETE'],
        url_path='messages/(?P<message_id>\d+)'
    )
    def manage_message(self, request, pk, message_id):
        """
        Метод получения отдельного сообщения, его удаления или
        редактирования.
        """
        chat = self.get_object()
        message = get_object_or_404(Message, chat=chat, id=message_id)
        if request.method == 'GET':
            serializer = serializers.MessageSerializer(message)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            if message.author != request.user:
                return Response(
                    {"detail": "Только автор может удалять сообщения"},
                    status=status.HTTP_403_FORBIDDEN
                )
            message.delete()
            return Response(
                {"detail": "Сообщение успешно удалено"},
                status=status.HTTP_204_NO_CONTENT
            )
        elif request.method in ['PUT', 'PATCH']:
            if message.author != request.user:
                return Response(
                    {"detail": "Только автор может редактировать сообщения"},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = serializers.MessageSerializer(
                message,
                data=request.data,
                partial=request.method == 'PATCH'
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = IsAuthenticatedOrReadOnly
    pagination_class = pagination.UsersPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = custom_filters.UserFilter

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()
