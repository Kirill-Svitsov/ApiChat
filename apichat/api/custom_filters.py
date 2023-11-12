from django.db import models
from django_filters import rest_framework

from messenger.models import Chat, Message
from users.models import User


class ChatFilter(rest_framework.FilterSet):
    """
    Класс фильтрации queryset по полям username,
    first_name, last_name. Поиск производится
    по частичному совпадению, регистр не учитывается.
    """
    username = rest_framework.CharFilter(method='filter_username', lookup_expr='iexact')
    first_name = rest_framework.CharFilter(method='filter_first_name', lookup_expr='iexact')
    last_name = rest_framework.CharFilter(method='filter_last_name', lookup_expr='iexact')

    class Meta:
        model = Chat
        fields = ('username', 'first_name', 'last_name')

    @staticmethod
    def filter_username(queryset, name, value):
        """Фильтрация выборки по полю username."""
        return queryset.filter(
            models.Q(sender__username__icontains=value)
            | models.Q(recipient__username__icontains=value)
        )

    @staticmethod
    def filter_first_name(queryset, name, value):
        """Фильтрация выборки по полю first_name."""
        return queryset.filter(
            models.Q(sender__first_name__icontains=value)
            | models.Q(recipient__first_name__icontains=value)
        )

    @staticmethod
    def filter_last_name(queryset, name, value):
        """Фильтрация выборки по полю last_name."""
        return queryset.filter(
            models.Q(sender__last_name__icontains=value)
            | models.Q(recipient__last_name__icontains=value)
        )


class MessageFilter(rest_framework.FilterSet):
    """Класс фильтрации сообщений по полям text и author"""
    text = rest_framework.CharFilter(field_name='text', lookup_expr='icontains')
    author = rest_framework.CharFilter(field_name='author__username', lookup_expr='icontains')

    class Meta:
        model = Message
        fields = ('text', 'author')


class UserFilter(rest_framework.FilterSet):
    """Класс фильтрации пользователей по полям username, first_name и last_name"""
    username = rest_framework.CharFilter(field_name='username', lookup_expr='icontains')
    first_name = rest_framework.CharFilter(field_name='first_name', lookup_expr='icontains')
    last_name = rest_framework.CharFilter(field_name='last_name', lookup_expr='icontains')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name')
