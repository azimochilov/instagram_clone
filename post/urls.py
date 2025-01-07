from django.urls import path
from .views import PostListAPIView,PostCreateAPIView, PostCommentListAPIView,PostRetrieveUpdateDestroyAPIView, PostCommentCreateAPIView,\
    CommentListCreateAPIView, PostLikeListAPIView, CommentRetrieveAPIView, CommentLikeListAPIView, PostLikeAPIView, CommentLikeAPIView
urlpatterns = [
    path('list/', PostListAPIView.as_view()),
    path('create/', PostCreateAPIView.as_view()),
    path('<uuid:pk>/', PostRetrieveUpdateDestroyAPIView.as_view()),
    path('<uuid:pk>/comments/', PostCommentListAPIView.as_view()),
    path('<uuid:pk>/likes/', PostLikeListAPIView.as_view()),
    path('<uuid:pk>/comments/create/', PostCommentCreateAPIView.as_view()),
    path('comments/', CommentListCreateAPIView.as_view()),
    path('comments/<uuid:pk>/', CommentRetrieveAPIView.as_view()),
    path('comments/<uuid:pk>/likes/', CommentLikeListAPIView.as_view()),
    path('<uuid:pk>/create-delete-like/', PostLikeAPIView.as_view()),
    path('comments/<uuid:pk>/create-delete-like/', CommentLikeAPIView.as_view()),
]