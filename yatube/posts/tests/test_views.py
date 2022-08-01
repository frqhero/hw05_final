from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.paginator import Page
from ..forms import PostForm
from ..models import Post, Group


User = get_user_model()


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый текст',
            slug='test-slug'
        )
        Post.objects.bulk_create([(Post(
            author_id=cls.user.id,
            id=x,
            group_id=cls.group.id,
            text='test post' + str(x)
        )) for x in range(1, 14)])

    def no_same_posts(cls, page1, page2):
        result = True
        merged_list = list(page1) + list(page2)
        list_to_check = []
        for each in merged_list:
            if each in list_to_check:
                result = False
            list_to_check.append(each)
        return result

    def test_namespace_and_template(self):
        """Проверка namespace и шаблона."""
        path_to_template_dict = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    args=[self.group.slug]): 'posts/group_list.html',
            reverse('posts:profile',
                    args=[self.user.username]): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': '1'}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': '1'}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for path, template in path_to_template_dict.items():
            with self.subTest(path=path, template=template):
                response = self.authorized_client.get(path)
                self.assertTemplateUsed(response, template)

    def test_index_page(self):
        """2.1, "posts/index.html", список постов и тест пажинатора."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIsInstance(response.context['page_obj'][0], Post)
        self.assertIsInstance(response.context['page_obj'], Page)
        self.assertEqual(len(response.context['page_obj']), 10)
        response_2nd_page = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(len(response_2nd_page.context['page_obj']), 3)
        self.assertTrue(self.no_same_posts(
            response.context['page_obj'],
            response_2nd_page.context['page_obj']), 'Дублируются посты')

    def test_group_list_page(self):
        """2.2, "posts/group_list.html", список постов отфильтрованных по
        группе и тест пажинатора."""
        response = self.authorized_client.get(
            reverse('posts:group_list', args=['test-slug']))
        self.assertIsInstance(response.context['page_obj'][0], Post)
        self.assertIsInstance(response.context['page_obj'], Page)
        self.assertEqual(response.context['page_obj'][0].group, self.group)
        response_2nd_page = self.authorized_client.get(
            reverse('posts:group_list', args=['test-slug']) + '?page=2')
        self.assertEqual(len(response_2nd_page.context['page_obj']), 3)
        self.assertTrue(self.no_same_posts(
            response.context['page_obj'],
            response_2nd_page.context['page_obj']), 'Дублируются посты')

    def test_profile_page(self):
        """2.3, "posts/profile.html", список постов отфильтрованных по
        пользователю и тест пажинатора."""
        response = self.authorized_client.get(
            reverse('posts:profile', args=['leo']))
        self.assertIsInstance(response.context['page_obj'][0], Post)
        self.assertIsInstance(response.context['page_obj'], Page)
        self.assertEqual(response.context['page_obj'][0].author, self.user)
        response_2nd_page = self.authorized_client.get(
            reverse('posts:profile', args=['leo']) + '?page=2')
        self.assertEqual(len(response_2nd_page.context['page_obj']), 3)
        self.assertTrue(self.no_same_posts(
            response.context['page_obj'],
            response_2nd_page.context['page_obj']), 'Дублируются посты')

    def test_post_detail(self):
        """2.4, "posts/post_detail.html", один пост, отфильтрованный по id."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=['1']))
        self.assertEqual(response.context['post'].id, 1)

    def test_form_edit(self):
        """2.5, "posts/create_post.html", форма редактирования поста,
        отфильтрованного по id."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=['1']))
        text_in_post = response.context['widget']['value']
        self.assertEqual(text_in_post, 'test post1')
        self.assertIsInstance(response.context['form'], PostForm)

    def test_form_create(self):
        """2.6, "posts/create_post.html", форма создания поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        text_in_post = response.context['widget']['value']
        self.assertFalse(text_in_post)
        self.assertIsInstance(response.context['form'], PostForm)

    def test_after_post_created(self):
        """Проверка появления поста в трех местах."""
        group = Group.objects.create(
            title='One more group',
            description='whatever',
            slug='one-more-group'
        )
        user = User.objects.create_user(username='pushkin', id=111)
        Post.objects.create(
            author_id=user.id,
            pk=777,
            group_id=group.id,
            text='who did that? pushkin of course'
        )
        reverses = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': 'one-more-group'}),
            reverse('posts:profile',
                    kwargs={'username': 'pushkin'})
        ]
        for destination in reverses:
            with self.subTest(destination=destination):
                response = self.guest_client.get(destination)
                self.assertEqual(response.context['page_obj'][0].id, 777)
