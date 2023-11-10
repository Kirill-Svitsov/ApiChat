from django.urls import path, include
from rest_framework import routers

from api.views import ChatViewSet, MessageViewSet, UserViewSet

router = routers.DefaultRouter()
router.register(r'chats', ChatViewSet, basename='chats')
router.register(r'messages', MessageViewSet, basename='messages')
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
