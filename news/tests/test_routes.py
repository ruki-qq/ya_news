from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from news.models import Comment, News

UserModel = get_user_model()


class TestRoutes(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(
            title='flutter',
            text='Our first song',
        )
        cls.author = UserModel.objects.create(username='julie')
        cls.reader = UserModel.objects.create(username='just_a_reader')
        cls.comment = Comment.objects.create(
            news=cls.news,
            author=cls.author,
            text='hi there',
        )

    def test_pages_availability(self):
        urls = (
            ('news:home', None),
            ('news:detail', {'pk': self.news.pk}),
            ('users:signup', None),
            ('users:login', None),
            ('users:logout', None),
        )
        for name, kwargs in urls:
            with self.subTest(name=name):
                url = reverse(name, kwargs=kwargs)
                res = self.client.get(url)

                self.assertEqual(res.status_code, HTTPStatus.OK)

    def test_comment_edit_delete(self):
        statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in statuses:
            self.client.force_login(user)
            for name in ('news:edit', 'news:delete'):
                url = reverse(name, kwargs={'pk': self.comment.pk})
                res = self.client.get(url)

                self.assertEqual(res.status_code, status)

    def test_comment_redirects(self):
        login_url = reverse('users:login')
        for name in ('news:edit', 'news:delete'):
            with self.subTest(name):
                url = reverse(name, kwargs={'pk': self.comment.pk})
                redirect_url = f'{login_url}?next={url}'
                res = self.client.get(url)

                self.assertRedirects(res, expected_url=redirect_url)
