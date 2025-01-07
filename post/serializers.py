from rest_framework import serializers

from post.models import Post, PostLike, PostComment, CommentLike
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'photo')


class PostSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)
    post_likes_count = serializers.SerializerMethodField('get_post_likes_count')
    post_comments_count = serializers.SerializerMethodField('get_post_comments_count')
    me_liked = serializers.SerializerMethodField('get_me_liked')

    class Meta:
        model = Post
        fields = ('id', 'author', 'image', 'caption', 'created_at','post_likes_count','post_comments_count', 'me_liked')

        extra_kwargs = {"image": {"required": False}}
    @staticmethod
    def get_post_likes_count(self, obj):
        return obj.likes.count()
    @staticmethod
    def get_post_comments_count(obj):
        return obj.comments.count()

    def get_me_liked(self, obj):
        request = self.context.get('request',None)
        if request.user.is_authenticated and request:
            try:
                like = PostLike.objects.get(post=obj, author=request.user)
                return True
            except PostLike.DoesNotExist:
                return False

        return False


class CommentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField('get_replies')
    me_liked = serializers.SerializerMethodField('get_me_liked')
    likes_count = serializers.SerializerMethodField('get_likes_count')

    class Meta:
        model = PostComment
        fields = ('id', 'author', 'comment', 'post', 'created_at','parent','replies','likes_count','me_liked')

    def get_replies(self, obj):
        if obj.child.exists():

            serializers = self.__class__(obj.child.all(), many=True, context=self.context)

            return serializers.data
        else:
            return None

    def get_me_liked(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.likes.filter(author=user).exists()
        else:
            return False
    @staticmethod
    def get_likes_count( obj):
        return obj.likes.count()


class CommentLikeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = CommentLike
        fields = ('id', 'author','comment')



class PostLikeSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = PostLike
        fields = ('id', 'author','post')

