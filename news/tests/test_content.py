from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from news.models import Comment, News


UserModel = get_user_model()


class TestHomePage(TestCase):
    HOME_URL = reverse('news:home')

    @classmethod
    def setUpTestData(cls):
        News.objects.bulk_create(
            [
                News(
                    title=f'News {i}',
                    text='Sample text',
                    date=timezone.now() - timedelta(days=i),
                )
                for i in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
            ]
        )

    def test_news_count(self):
        res = self.client.get(self.HOME_URL)
        news_count = len(res.context['object_list'])

        self.assertEqual(news_count, settings.NEWS_COUNT_ON_HOME_PAGE)

    def test_news_order(self):
        res = self.client.get(self.HOME_URL)
        all_dates = [news.date for news in res.context['object_list']]
        sorted_dates = sorted(all_dates, reverse=True)

        self.assertEqual(all_dates, sorted_dates)


class TestDetail(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(title='Test', text='Sample text')
        cls.url = reverse('news:detail', kwargs={'pk': cls.news.pk})
        cls.author = UserModel.objects.create(username='tester')
        for i in range(2):
            comment = Comment.objects.create(
                news=cls.news,
                author=cls.author,
                text=f'hi there {i}',
            )
            comment.created = timezone.now() + timedelta(days=i)
            comment.save()

    def test_comment_order(self):
        res = self.client.get(self.url)
        news = res.context['news']
        all_comments = news.comment_set.all()

        self.assertLess(all_comments[0].created, all_comments[1].created)

    def test_form_anon(self):
        res = self.client.get(self.url)

        self.assertNotIn('form', res.context)

    def test_form_authorised(self):
        self.client.force_login(self.author)

        res = self.client.get(self.url)

        self.assertIn('form', res.context)
