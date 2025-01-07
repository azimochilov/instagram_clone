from django.contrib import admin
from .models import Post,PostLike,PostComment,CommentLike
from django.contrib import admin
from .models import Post, PostLike, PostComment, CommentLike


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'caption', 'created_at', 'updated_at')
    search_fields = ('author__username', 'caption')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'comment', 'parent', 'created_at', 'updated_at')
    search_fields = ('author__username', 'post__caption', 'comment')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'created_at')
    search_fields = ('author__username', 'post__caption')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'comment', 'created_at')
    search_fields = ('author__username', 'comment__comment')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
