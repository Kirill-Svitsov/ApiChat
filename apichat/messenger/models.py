from django.db import models
from users.models import User


class Chat(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_chats')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_chats')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'
        ordering = ('-created_at',)

    def __str__(self):
        return f'Chat {self.id}'


class Message(models.Model):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='message'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authored_messages'
    )
    text = models.TextField(verbose_name='Текст сообщения')
    date_sent = models.DateTimeField(auto_now_add=True, verbose_name='Дата отправки')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    likes = models.ManyToManyField(User, related_name='liked_messages', blank=True)
    dislikes = models.ManyToManyField(User, related_name='disliked_messages', blank=True)

    class Meta:
        ordering = ('-date_sent',)
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'

    def __str__(self):
        return f'{self.chat.sender.username} - {self.text[:20]}...'


class Image(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='message_images/', verbose_name='Фото')

    class Meta:
        verbose_name = 'Фото к сообщению'
        verbose_name_plural = 'Фото к сообщениям'

    def __str__(self):
        return f'Image {self.id}'
