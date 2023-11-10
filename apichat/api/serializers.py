from django.db.transaction import atomic
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from messenger.models import Chat, Image, Message
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'avatar']

    def create(self, validated_data):
        avatar_data = validated_data.pop('avatar', None)
        user = User.objects.create(**validated_data)
        if avatar_data:
            user.avatar = avatar_data
            user.save()
        return user


class ImageSerializer(serializers.ModelSerializer):
    image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = Image
        fields = ['id', 'image']


class MessageSerializer(serializers.ModelSerializer):
    chat = serializers.SerializerMethodField(read_only=True)
    author = UserSerializer(read_only=True)
    images = ImageSerializer(many=True, required=False)

    class Meta:
        model = Message
        fields = ['id', 'text', 'date_sent', 'is_read', 'likes', 'dislikes', 'images', 'chat', 'author']

    @atomic
    def create(self, validated_data):
        user = self.context['request'].user
        images_data = validated_data.pop('images', None)
        # Извлекаем чат из входных данных
        chat = validated_data.pop('chat', None)
        # Если чат не указан, предполагаем, что он уже существует
        if not chat:
            raise serializers.ValidationError("Chat is required for creating a message.")
        message = Message.objects.create(
            author=user,
            text=validated_data['text'],
            chat=chat
        )
        if images_data:
            for image_data in images_data:
                Image.objects.create(message=message, **image_data)
        return message

    @staticmethod
    def get_chat(obj):
        chat = obj.chat
        return chat.id if chat else None


class ChatSerializer(serializers.ModelSerializer):
    recipient = UserSerializer()
    sender = UserSerializer()
    messages_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ('id', 'recipient', 'sender', 'created_at', 'messages_count')

    @staticmethod
    def get_messages_count(chat):
        return chat.message.count()


class ChatCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания чата"""
    recipient = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )
    sender = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Chat
        fields = (
            'sender',
            'recipient',
        )

    def validate(self, data):
        user = self.context['request'].user
        recipient_id = data['recipient'].id  # Обращение к полю recipient для получения id

        # Проверка: Нельзя создать чат с самим собой
        if user.id == recipient_id:
            raise serializers.ValidationError("Нельзя создать чат с самим собой")

        # Проверка: Нельзя создать чат с несуществующим пользователем
        try:
            User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("Такого пользователя не существует")

        # Устанавливаем текущего пользователя в качестве отправителя (sender)
        data['sender'] = user

        return data

    @atomic
    def create(self, validated_data):
        # sender уже установлен в методе validate, не нужно его повторно получать
        recipient = validated_data['recipient']
        chat = Chat.objects.create(sender=validated_data['sender'], recipient=recipient)
        return chat

    def to_representation(self, chat):
        request = self.context.get('request')
        return ChatSerializer(
            chat, context={'request': request}
        ).data
