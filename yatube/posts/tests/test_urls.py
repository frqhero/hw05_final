from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.contrib.auth.models import User
from posts.models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый текст',
            slug='test-slug'
        )
        cls.user = User.objects.create_user(username='HasNoName')
        cls.post = Post.objects.create(
            author_id=cls.user.id,
            id=1,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_guest_client_200_and_correct_template(self):
        """Проверка доступа и шаблона для страниц (неавторизованно)"""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url, template=template):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page(self):
        """Несуществующая страница выдает ошибку 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)

    def test_authorized_client_200_and_correct_template(self):
        """Проверка доступа и шаблона для страниц (авторизованно)."""
        templates_url_names = {
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url, template=template):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template)

    def test_not_author_redirected(self):
        """Не автор получает редирект при попытке изменить пост."""
        someone_else = User.objects.create_user(username='orwell')
        client = Client()
        client.force_login(someone_else)
        response = client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_unauth_user_redirected(self):
        """Гость получает редирект при попытке создания поста."""
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')
