from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

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
