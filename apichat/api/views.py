from djoser.views import UserViewSet as DjoserUserViewSet
from django.db import models
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api import serializers
from messenger.models import Chat, Message
from users.models import User


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.select_related(
        'recipient',
        'sender'
    ).prefetch_related('message__author').all()

    def get_serializer_class(self):
        """Получение сериализатора в зависимости от запроса"""
        if self.action in ('list', 'retrieve'):
            return serializers.ChatSerializer
        return serializers.ChatCreateSerializer

    def get_queryset(self):
        """Возвращает чаты, в которых присутствует пользователь"""
        user = self.request.user
        return Chat.objects.filter(
            models.Q(sender=user) | models.Q(recipient=user)
        )

    def get_object(self):
        """Проверка разрешений для доступа к конкретному чату"""
        obj = super().get_object()
        user = self.request.user
        if user != obj.sender and user != obj.recipient:
            raise PermissionDenied("Вы не являетесь участником этого чата")
        return obj

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, context={'request': request})

        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['GET', 'POST'],
        permission_classes=(IsAuthenticated,),
        url_path='messages'
    )
    def handle_messages(self, request, pk):
        chat = self.get_object()
        user = request.user
        if user != chat.sender and user != chat.recipient:
            raise PermissionDenied("Вы не являетесь участником этого чата")
        if request.method == 'GET':
            messages = Message.objects.filter(chat=chat)
            serializer = serializers.MessageSerializer(messages, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            user = request.user
            # Проверяем, что текущий пользователь принадлежит к чату
            if user != chat.sender and user != chat.recipient:
                return Response(
                    {"detail": "You do not have permission to send messages in this chat."},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = serializers.MessageSerializer(
                data=request.data,
                context={'request': request}
            )
            if serializer.is_valid():
                message = serializer.save(chat=chat, author=user)
                return Response(serializers.MessageSerializer(message).data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['GET', 'PUT', 'PATCH', 'DELETE'],
        url_path='messages/(?P<message_id>\d+)'
    )
    def manage_message(self, request, pk, message_id):
        chat = self.get_object()
        try:
            message = Message.objects.get(chat=chat, id=message_id)
        except Message.DoesNotExist:
            return Response(
                {"detail": "Сообщение не найдено"},
                status=status.HTTP_404_NOT_FOUND
            )
        if request.method == 'GET':
            serializer = serializers.MessageSerializer(message)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            if message.author != request.user:
                return Response({"detail": "Только автор может удалять сообщения"},
                                status=status.HTTP_403_FORBIDDEN)
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
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = serializers.MessageSerializer


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()
