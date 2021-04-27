
from rest_framework import serializers
from .models import Problem, CodeImage, Reply, Comment, Like

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeImage
        fields = ('image', 'id')

    def _get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            url = obj.image.url
            if request is not None:
                url = request.build_absolute_uri(url)
            return url
        return ''

    def to_representation(self, instance):
        representation = super(ImageSerializer, self).to_representation(instance)
        representation['image'] = self._get_image_url(instance)
        return representation


class ProblemSerializer(serializers.ModelSerializer):
    created = serializers.DateTimeField(format="%d/%B/%Y",
                                        read_only=True)
    images = ImageSerializer(many=True, read_only=True)
    author = serializers.ReadOnlyField(source='author.email')

    class Meta:
        model = Problem
        fields = ('id', 'title', 'description', 'images',
                  'created', 'author')

    def create(self, validated_data):
        request = self.context.get('request')
        images_data = request.FILES
        author = request.user
        print(author)
        problem = Problem.objects.create(
            author=author, **validated_data
        )
        for image in images_data.getlist('images'):
            CodeImage.objects.create(problem=problem,
                                     image=image)
        return problem

    def update(self, instance, validated_data):
        request = self.context.get('request')
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.images.all().delete()
        images_data = request.FILES
        for image in images_data.getlist('images'):
            CodeImage.objects.create(
                problem=instance, image=image
            )
        return instance

    def to_representation(self, instance):
        representation = super(ProblemSerializer, self).to_representation(instance)
        representation['Replies'] = ReplySerializer(instance.replies.all(),
                                                    many=True).data

        action = self.context.get('action')
        like = LikeSerializer(instance.likes.filter(like=True), many=True, context=self.context).data
        replies = ReplySerializer(instance.replies.all(), many=True,
                                    context=self.context).data

        if action == 'retrieve':
            self.context['action'] = 'list'
            representation['Images'] = ImageSerializer(instance.images.all(), many=True, context=self.context).data
            representation['Like'] = like
        return representation


class ReplySerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.email')

    class Meta:
        model = Reply
        fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')
        author = request.user
        reply = Reply.objects.create(
            author=author, **validated_data
        )
        return reply

    def to_representation(self, instance):
        representation = super(ReplySerializer,self).to_representation(instance)
        representation['Comments'] = CommentSerializer(instance.comments.all(), many=True).data
        return representation


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.email')

    class Meta:
        model = Comment
        fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')
        author = request.user
        comment = Comment.objects.create(author=author, **validated_data)
        return comment


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ('id', 'problem', 'user', 'like')

    def get_fields(self):
        action = self.context.get('action')
        fields = super().get_fields()
        if action == 'create':
            fields.pop('user')
            fields.pop('like')
        return fields

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        problem = validated_data.get('problem')
        like = Like.objects.get_or_create(user=user, problem=problem)[0]
        like.like = True if like.like is False else False
        like.save()
        return like


