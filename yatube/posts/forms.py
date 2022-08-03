from django import forms
from posts.models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        # где то наоборот было что определять в моделе, а мол
        # в форме редко переопределяется


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
