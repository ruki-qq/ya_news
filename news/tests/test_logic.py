from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import News, Comment

UserModel = get_user_model()


# noinspection DuplicatedCode
class TestCommentCreation(TestCase):
    COMMENT_TEXT = 'Sample text'

    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(
            title='Test',
            text='Sample text',
        )
        cls.url = reverse('news:detail', kwargs={'pk': cls.news.pk})
        cls.user = UserModel.objects.create(username='tester')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {'text': cls.COMMENT_TEXT}

    def test_create_comment_anon(self):
        self.client.post(self.url, data=self.form_data)
        comm_count = Comment.objects.count()

        self.assertEqual(comm_count, 0)

    def test_create_comment_user(self):
        res = self.auth_client.post(self.url, data=self.form_data)

        self.assertRedirects(res, f'{self.url}#comments')

        comm_count = Comment.objects.count()

        self.assertEqual(comm_count, 1)

        comm = Comment.objects.get()

        self.assertEqual(comm.text, self.COMMENT_TEXT)
        self.assertEqual(comm.news, self.news)
        self.assertEqual(comm.author, self.user)

    def test_comment_bad_words(self):
        bad_words_data = {
            'text': f'Sample, {BAD_WORDS[0]}, text',
        }
        res = self.auth_client.post(self.url, data=bad_words_data)

        self.assertFormError(
            res,
            form='form',
            field='text',
            errors=WARNING,
        )

        comments_count = Comment.objects.count()

        self.assertEqual(comments_count, 0)


class TestCommentEditDelete(TestCase):
    COMMENT_TEXT = 'Sample text'
    NEW_COMMENT_TEXT = 'New text'

    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(
            title='Test',
            text='Sample text',
        )
        cls.url = (
            reverse('news:detail', kwargs={'pk': cls.news.pk}) + '#comments'
        )
        cls.author = UserModel.objects.create(username='comm_author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = UserModel.objects.create(username='reader')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.comment = Comment.objects.create(
            news=cls.news, author=cls.author, text=cls.COMMENT_TEXT
        )
        cls.edit_url = reverse('news:edit', kwargs={'pk': cls.comment.pk})
        cls.delete_url = reverse('news:delete', kwargs={'pk': cls.comment.pk})
        cls.form_data = {'text': cls.NEW_COMMENT_TEXT}

    def test_delete_comment_author(self):
        res = self.author_client.delete(self.delete_url)

        self.assertRedirects(res, self.url)

        comm_count = Comment.objects.count()

        self.assertEqual(comm_count, 0)

    def test_delete_comment_reader(self):
        res = self.reader_client.delete(self.delete_url)

        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        comm_count = Comment.objects.count()

        self.assertEqual(comm_count, 1)

    def test_edit_comment_author(self):
        res = self.author_client.post(self.edit_url, data=self.form_data)

        self.assertRedirects(res, self.url)

        self.comment.refresh_from_db()

        self.assertEqual(self.comment.text, self.NEW_COMMENT_TEXT)

    def test_edit_comment_reader(self):
        res = self.reader_client.post(self.edit_url, data=self.form_data)

        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        self.comment.refresh_from_db()

        self.assertEqual(self.comment.text, self.COMMENT_TEXT)
