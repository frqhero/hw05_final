import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Follow, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='У Лукоморья дуб зеленый',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        tests = {
            self.group.title: str(self.group),
            self.post.text[:15]: str(self.post),
        }
        for exp_obj_str, gotten_rep in tests.items():
            with self.subTest(exp=exp_obj_str, rep=gotten_rep):
                self.assertEqual(exp_obj_str, gotten_rep)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class SubsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_p = User.objects.create_user(username='pushkin')
        cls.user_l = User.objects.create_user(username='leo')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_client_p = Client()
        self.auth_client_p.force_login(self.user_p)
        self.auth_client_l = Client()
        self.auth_client_l.force_login(self.user_l)

    def test_auth_can_sub_and_unsub(self):
        follows_cnt = Follow.objects.count()
        self.auth_client_p.get(reverse('posts:profile_follow',
                                       args=(self.user_l.username,)))
        self.assertEqual(Follow.objects.count(), follows_cnt + 1)

        entry = Follow.objects.get(user=self.user_p)
        self.assertEqual(entry.author, self.user_l)

        self.auth_client_p.get(reverse('posts:profile_unfollow',
                               args=(self.user_l.username,)))
        self.assertEqual(Follow.objects.count(), follows_cnt)

    def test_post_appears_in_right_feed(self):
        # pushkin subs on leo
        self.auth_client_p.get(reverse('posts:profile_follow',
                                       args=(self.user_l.username,)))
        leo_post = Post.objects.create(author=self.user_l, text='awesome post',
                                       id=777)
        response = self.auth_client_p.get(reverse('posts:follow_index'))
        self.assertTrue(leo_post in response.context['page_obj'])

        pushkin_post = Post.objects.create(author=self.user_p,
                                           text='awesome post', id=555)
        response = self.auth_client_l.get(reverse('posts:follow_index'))
        self.assertTrue(pushkin_post not in response.context['page_obj'])
