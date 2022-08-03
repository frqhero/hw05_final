import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post

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


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PictureWorksTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='pushkin')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый текст',
            slug='test-slug'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='from setup',
            image=cls.uploaded,
        )
        cls.r_add_comment = reverse('posts:add_comment',
                                    args=(cls.post.id,))
        cls.r_post_detail = reverse('posts:post_detail', args=(cls.post.id,))
        cls.form_data = {'text': 'new comment'}

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

    def test_pictures_created_by_form(self):
        b4_test = Post.objects.count()
        form_data = {
            'author': self.user,
            'text': 'Тестовый текст',
            'image': self.uploaded,
        }
        # Отправляем POST-запрос
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), b4_test + 1)
        self.assertRedirects(response, reverse('posts:profile',
                                               args=[self.user.username]))

    def test_context_gets_picture(self):
        exp_pic_name = 'posts/small.gif'
        reverses = [
            reverse('posts:index'),
            reverse('posts:profile', args=[self.user.username]),
            reverse('posts:group_list', args=[self.group.slug]),
        ]
        for cur_reverse in reverses:
            with self.subTest(cur_reverse=cur_reverse):
                response = self.auth_client.get(cur_reverse)
                pic_name = self.get_pic_name(response)
                self.assertEqual(pic_name, exp_pic_name)

        p_d_response = self.auth_client.get(self.r_post_detail)
        post_pic_name = p_d_response.context['post'].image.name
        self.assertEqual(post_pic_name, exp_pic_name)

    def get_pic_name(self, r):
        return r.context['page_obj'][0].image.name

    def test_comment_creation_unavailable_for_unauth_user(self):
        comments_cnt = Comment.objects.count()
        self.guest_client.post(self.r_add_comment, data=self.form_data)
        self.assertEqual(Comment.objects.count(), comments_cnt)

    def test_new_comment_appears(self):
        self.auth_client.post(self.r_add_comment, data=self.form_data)

        response = self.guest_client.get(self.r_post_detail)
        com = response.context['comments'][0]
        self.assertEqual(com.text, self.form_data['text'])
