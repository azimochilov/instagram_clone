from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView, \
    RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Post, PostLike, PostComment, CommentLike
from .serializers import PostSerializer, PostLikeSerializer, CommentSerializer, CommentLikeSerializer
from shared.custom_pagination import CustomPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class PostListAPIView(ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [AllowAny, ]
    pagination_class = CustomPagination

    @swagger_auto_schema(
        operation_summary="List all posts",
        operation_description="Retrieve a paginated list of all posts.",
        responses={200: PostSerializer(many=True)}
    )
    def get_queryset(self):
        return Post.objects.all()


class PostCreateAPIView(CreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, ]

    @swagger_auto_schema(
        operation_summary="Create a post",
        operation_description="Allows an authenticated user to create a new post.",
        request_body=PostSerializer,
        responses={
            201: openapi.Response(description="Created", schema=PostSerializer())
        }
    )
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, ]

    @swagger_auto_schema(
        operation_summary="Retrieve a post",
        operation_description="Retrieve the details of a specific post by its ID.",
        responses={status.HTTP_200_OK: openapi.Response('Success', PostSerializer)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a post",
        operation_description="Update an existing post. Requires authentication.",
        request_body=PostSerializer,
        responses={status.HTTP_200_OK: openapi.Response('Success', PostSerializer)}
    )
    def put(self, request, *args, **kwargs):
        post = self.get_object()
        serializer = self.serializer_class(post, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Delete a post",
        operation_description="Delete a specific post by its ID. Requires authentication.",
        responses={status.HTTP_204_NO_CONTENT: openapi.Response('Post deleted successfully')}
    )
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

    @swagger_auto_schema(
        operation_summary="List comments for a post",
        operation_description="Retrieve all comments for a specific post by its ID.",
        responses={200: CommentSerializer(many=True)}
    )
    def get_queryset(self):
        post_id = self.kwargs['pk']
        queryset = PostComment.objects.filter(post_id=post_id)
        return queryset


class PostCommentCreateAPIView(CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated,]

    @swagger_auto_schema(
        operation_summary="Create a comment for a post",
        operation_description="Allows an authenticated user to create a comment for a specific post.",
        request_body=CommentSerializer,
        responses={201: CommentSerializer}
    )
    def perform_create(self, serializer):
        post_id = self.kwargs['pk']
        serializer.save(author=self.request.user, post_id=post_id)


class CommentListCreateAPIView(ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, ]
    queryset = PostComment.objects.all()
    pagination_class = CustomPagination

    @swagger_auto_schema(
        operation_summary="List and create comments",
        operation_description="List all comments and allows authenticated users to create a new comment.",
        request_body=CommentSerializer,
        responses={200: CommentSerializer(many=True), 201: CommentSerializer}
    )
    def get_queryset(self):
        return self.queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostLikeListAPIView(ListAPIView):
    serializer_class = PostLikeSerializer
    permission_classes = [AllowAny,]

    @swagger_auto_schema(
        operation_summary="List likes for a post",
        operation_description="Retrieve all likes for a specific post by its ID.",
        responses={200: PostLikeSerializer(many=True)}
    )
    def get_queryset(self):
        post_id = self.kwargs['pk']
        queryset = PostLike.objects.filter(post_id=post_id)
        return queryset


class CommentRetrieveAPIView(RetrieveAPIView):
    serializer_class = CommentSerializer
    permission_classes = [AllowAny, ]
    queryset = PostComment.objects.all()

    @swagger_auto_schema(
        operation_summary="Retrieve a specific comment",
        operation_description="Retrieve a specific comment by its ID.",
        responses={200: CommentSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CommentLikeListAPIView(ListAPIView):
    serializer_class = CommentLikeSerializer
    permission_classes = [AllowAny,]

    @swagger_auto_schema(
        operation_summary="List likes for a comment",
        operation_description="Retrieve all likes for a specific comment by its ID.",
        responses={200: CommentLikeSerializer(many=True)}
    )
    def get_queryset(self):
        comment_id = self.kwargs['pk']
        queryset = CommentLike.objects.filter(comment_id=comment_id)
        return queryset


class PostLikeAPIView(APIView):
    @swagger_auto_schema(
        operation_summary="Like a post",
        operation_description="Allows an authenticated user to like a specific post.",
        responses={201: PostLikeSerializer}
    )
    def post(self, request, pk):
        try:
            post_like = PostLike.objects.create(
                author=self.request.user,
                post_id=pk,
            )
            serializer = PostLikeSerializer(post_like)
            data = {
                "success": True,
                "message": "Post liked successfully.",
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

    @swagger_auto_schema(
        operation_summary="Unlike a post",
        operation_description="Allows an authenticated user to remove their like from a specific post.",
        responses={204: "Like removed successfully"}
    )
    def delete(self, request, pk):
        try:
            post_like = PostLike.objects.get(author=self.request.user, post_id=pk)
            post_like.delete()
            data = {
                "success": True,
                "message": "You took your LIKE back",
                "data": None
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
    @swagger_auto_schema(
        operation_summary="Like a comment",
        operation_description="Allows an authenticated user to like a specific comment.",
        responses={201: CommentLikeSerializer}
    )
    def post(self, request, pk):
        try:
            comment_like = CommentLike.objects.create(
                author=self.request.user,
                comment_id=pk,
            )
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

    @swagger_auto_schema(
        operation_summary="Unlike a comment",
        operation_description="Allows an authenticated user to remove their like from a specific comment.",
        responses={204: "Like removed successfully"}
    )
    def delete(self, request, pk):
        try:
            comment_like = CommentLike.objects.get(author=self.request.user, comment_id=pk)
            comment_like.delete()
            data = {
                "success": True,
                "message": "You took your LIKE back",
                "data": None
            }
            return Response(data, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            data = {
                "success": False,
                "message": str(e),
                "data": None
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
