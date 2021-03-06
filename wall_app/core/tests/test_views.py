from django.urls import reverse_lazy
from rest_framework import status
import mock

from factories.factories import PostFactory, ProfileFactory, UserFactory

from core.models import Love, Post
from core.tests.http_header import APIHeaderAuthorization
from core.tests.testing_utils import (
    create_love_relationship, create_post_objects
)


class PostListTestSuite(APIHeaderAuthorization):
    @classmethod
    def setUpClass(cls):
        super(PostListTestSuite, cls).setUpClass()
        cls.url = reverse_lazy('post-list')

    def test_get_all_posts(self):
        num_posts = 3
        posts = create_post_objects(self.profile.user, num_posts)
        posts.reverse()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), num_posts)
        for index, post in enumerate(response.data['results']):
            self.assertEqual(post['content'], posts[index].content)

    def test_unauthenticated_user_can_also_view_posts(self):
        self.client.logout()
        num_posts = 3
        create_post_objects(self.profile.user, num_posts)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), num_posts)

    def test_post_new_post(self):
        post = {'content': 'Hello World!'}
        response = self.client.post(self.url, data=post)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Post.objects.filter(content=post['content']).exists()
        )

    @mock.patch('core.pagination.StandardResultsSetPagination.page_size')
    def test_posts_response_are_paginated(self, mocked_page_size):
        mocked_page_size.return_value = 1
        num_posts = 3
        create_post_objects(self.profile.user, num_posts)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data['results']),
            mocked_page_size.return_value
        )
        self.assertEqual(response.data['count'], num_posts)
        self.assertTrue(response.data['next'])

    def test_get_top_posts(self):
        user_2 = UserFactory(username='jane_doe')
        num_posts = 3
        posts = create_post_objects(self.profile.user, num_posts)
        post_with_no_love, post_with_1_love, post_with_2_loves = posts
        create_love_relationship(self.profile.user,
                                 [post_with_1_love, post_with_2_loves])
        create_love_relationship(user_2, [post_with_2_loves])

        response = self.client.get(self.url, {'q': 'top'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        posts.reverse()
        expected = [post.content for post in posts]
        returned = [post['content'] for post in response.data['results']]
        self.assertEqual(returned, expected)

    def test_get_top_2_posts(self):
        user_2 = UserFactory(username='jane_doe')
        num_posts = 3
        posts = create_post_objects(self.profile.user, num_posts)
        post_with_no_love, post_with_1_love, post_with_2_loves = posts
        create_love_relationship(self.profile.user,
                                 [post_with_1_love, post_with_2_loves])
        create_love_relationship(user_2, [post_with_2_loves])

        response = self.client.get(self.url, {'q': 'top', 'limit': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)


class PostDetailTestSuite(APIHeaderAuthorization):
    @classmethod
    def setUpClass(cls):
        super(PostDetailTestSuite, cls).setUpClass()
        cls.CONTENT = 'content'
        cls.AUTHOR = 'author'

    def setUp(self):
        super(PostDetailTestSuite, self).setUp()
        self.post = PostFactory(author=self.profile.user)
        self.url = reverse_lazy('post-detail', kwargs={'pk': self.post.id})

    def test_retrieve_single_post(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[self.CONTENT], self.post.content)

    def test_update_post(self):
        data = {self.CONTENT: 'Updated Post'}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[self.CONTENT], data[self.CONTENT])

    def test_delete_post(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(
            content=self.post.content).exists())


class LoveCreateTestSuite(APIHeaderAuthorization):
    def setUp(self):
        super(LoveCreateTestSuite, self).setUp()
        self.post = PostFactory(author=self.profile.user)
        self.data = {}

    def test_love_create_success(self):
        self.url = reverse_lazy(
            'love-view', kwargs={'post_id': self.post.id})
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        love = Love.objects.filter(fan=self.profile.user, post=self.post)
        self.assertTrue(love.exists())

    def test_love_create_response(self):
        self.url = reverse_lazy(
            'love-view', kwargs={'post_id': self.post.id})
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['num_loves'], 1)
        self.assertEqual(response.data['in_love'], True)

    def test_auth_user_can_love_anothers_post(self):
        user = UserFactory(username='new_user')
        ProfileFactory(user=user)
        post = PostFactory(content='New Post', author=user)

        self.url = reverse_lazy(
            'love-view', kwargs={'post_id': post.id})
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        love = Love.objects.filter(fan=self.profile.user, post=post)
        self.assertTrue(love.exists())


class LoveDeleteTestSuite(APIHeaderAuthorization):
    def setUp(self):
        super(LoveDeleteTestSuite, self).setUp()
        self.post = PostFactory(author=self.profile.user)
        self.love = Love.objects.create(fan=self.profile.user, post=self.post)

    def test_delete_love_success(self):
        self.url = reverse_lazy(
            'love-view', kwargs={'post_id': self.post.id})
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        love = Love.objects.filter(fan=self.profile.user, post=self.post)
        self.assertFalse(love.exists())

    def test_love_create_response(self):
        self.url = reverse_lazy(
            'love-view', kwargs={'post_id': self.post.id})
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['num_loves'], 0)
        self.assertEqual(response.data['in_love'], False)

    def test_auth_user_can_unlove_anothers_post(self):
        user = UserFactory(username='new_user')
        ProfileFactory(user=user)
        post = PostFactory(content='New Post', author=user)

        self.url = reverse_lazy(
            'love-view', kwargs={'post_id': post.id})
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        love = Love.objects.filter(fan=self.profile.user, post=post)
        self.assertFalse(love.exists())
