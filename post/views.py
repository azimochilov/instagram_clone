from django.shortcuts import render
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated,AllowAny

from .models import Post,PostLike,PostComment,CommentLike
from .serializers import PostSerializer,PostLikeSerializer,CommentSerializer,CommentLikeSerializer
from shared.custom_pagination import CustomPagination

class PostListAPIView(ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [AllowAny,]
    pagination_class = CustomPagination

    def get_queryset(self):
        return Post.objects.all()

class PostCreateAPIView(CreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated,]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
