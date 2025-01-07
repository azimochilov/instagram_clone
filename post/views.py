from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView, \
    RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

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


class PostRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]

    def put(self, request, *args, **kwargs):
        post = self.get_object()
        serializer = self.serializer_class(post, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        post = self.get_object()
        post.delete()
        return Response({
            'success': True,
            'message': 'Post deleted.',
            'code': status.HTTP_204_NO_CONTENT,
        })

class PostCommentListAPIView(ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [AllowAny,]
    def get_queryset(self):
        post_id = self.kwargs['pk']
        queryset = PostComment.objects.filter(post_id=post_id)
        return queryset

class PostCommentCreateAPIView(CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated,]

    def perform_create(self, serializer):
        post_id = self.kwargs['pk']
        serializer.save(author=self.request.user,post_id=post_id)

class CommentListCreateAPIView(ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, ]
    queryset = PostComment.objects.all()
    pagination_class = CustomPagination
    def get_queryset(self):
        return self.queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostLikeListAPIView(ListAPIView):
    serializer_class = PostLikeSerializer
    permission_classes = [AllowAny,]
    def get_queryset(self):
        post_id = self.kwargs['pk']
        queryset = PostLike.objects.filter(post_id=post_id)
        return queryset

class CommentRetrieveAPIView(RetrieveAPIView):
    serializer_class = CommentSerializer
    permission_classes = [AllowAny, ]
    queryset = PostComment.objects.all()


class CommentLikeListAPIView(ListAPIView):
    serializer_class = CommentLikeSerializer
    permission_classes = [AllowAny,]
    def get_queryset(self):
        comment_id = self.kwargs['pk']
        queryset = CommentLike.objects.filter(comment_id=comment_id)
        return queryset

class PostLikeAPIView(APIView):
    def post(self, request, pk):
        try:
            post_like = PostLike.objects.create(
                author=self.request.user,
                post_id=pk,)
            serializer = PostLikeSerializer(post_like)
            data = {
                "success": True,
                "message": "Post liked successfully.",
                "data":serializer.data
            }
            return Response(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            data = {
                "success": False,
                "message": str(e),
                "data": None
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        try:
            post_like = PostLike.objects.get(author=self.request.user,post_id=pk)
            post_like.delete()
            data = {
                "success": True,
                "message": "You took your LIKE back",
                "data":None
            }
            return Response(data, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            data = {
                "success": False,
                "message": str(e),
                "data": None
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class CommentLikeAPIView(APIView):
    def post(self, request, pk):
        try:
            comment_like = CommentLike.objects.create(
                author=self.request.user,
                comment_id=pk,)
            serializer = CommentLikeSerializer(comment_like)
            data = {
                "success": True,
                "message": "Comment liked successfully.",
                "data": serializer.data
            }
            return Response(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            data = {
                "success": False,
                "message": str(e),
                "data": None
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        try:
            comment_like = CommentLike.objects.get(author=self.request.user,comment_id=pk)
            comment_like.delete()
            data = {
                "success": True,
                "message": "You took your LIKE back",
                "data":None
            }
            return Response(data, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            data = {
                "success": False,
                "message": str(e),
                "data": None
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)