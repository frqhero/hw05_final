from ..models import Post
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class PostCreateTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='pushkin')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Первый пункт задания.
        Создание нового поста.
        Заполнение формы и пост запрос"""
        quantity_before = Post.objects.count()
        form_data = {
            'text': 'some poetry',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile', args=[self.user.username])
        )
        self.assertEqual(Post.objects.all()[0].text, form_data['text'])
        self.assertEqual(Post.objects.count(), quantity_before + 1)

    def test_edit_post(self):
        """Второй пункт задания. Редактирование имеющегося поста."""
        Post.objects.create(
            author_id=self.user.id,
            pk=777,
            text='initial text'
        )
        form_data = {'text': 'new text'}
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[777]),
            data=form_data,
        )
        new_post = Post.objects.get(pk=777)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail', args=[777])
        )
        self.assertEqual(new_post.text, 'new text')
