from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from forum.models import Reply, Tag, Thread, ThreadVote


class ThreadAPITests(APITestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user('ana', email='ana@example.com', password='Test-1234')
        self.other = get_user_model().objects.create_user('luis', email='luis@example.com', password='Test-1234')
        self.tag = Tag.objects.create(name='django')
        self.thread = Thread.objects.create(author=self.owner, title='Duda Django', content='Consulta sobre vistas')
        self.thread.tags.add(self.tag)
        self.url = reverse('api:thread-list')
        self.detail = reverse('api:thread-detail', args=[self.thread.pk])
        self.vote = reverse('api:thread-vote', args=[self.thread.pk])

    def test_public_list_and_detail_hide_private_user_data(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        item = response.data['results'][0]
        self.assertEqual(item['author'], {'id': self.owner.pk, 'username': 'ana'})
        self.assertEqual(item['tags_detail'][0]['name'], 'django')
        self.assertEqual(item['puntuacion'], 0)
        self.assertEqual(self.client.get(self.detail).status_code, 200)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.views_count, 0)  # GET de API no cuenta visitas web.

    def test_anonymous_cannot_write(self):
        for method, url, data in [('post', self.url, {'title': 'Nuevo', 'content': 'Texto'}),
                                  ('patch', self.detail, {'title': 'Otro'}),
                                  ('delete', self.detail, {}), ('post', self.vote, {'value': 1})]:
            with self.subTest(method=method, url=url):
                self.assertEqual(getattr(self.client, method)(url, data, format='json').status_code, 403)

    def test_create_assigns_author_and_protects_server_fields(self):
        self.client.force_authenticate(self.other)
        response = self.client.post(self.url, {
            'title': 'Nuevo', 'content': 'Contenido', 'tags': [self.tag.pk],
            'author': self.owner.pk, 'is_locked': True, 'views_count': 100,
            'is_deleted': True, 'accepted_reply': 999,
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        thread = Thread.objects.get(pk=response.data['id'])
        self.assertEqual(thread.author, self.other)
        self.assertFalse(thread.is_locked or thread.is_deleted)
        self.assertEqual(thread.views_count, 0)
        self.assertEqual(list(thread.tags.all()), [self.tag])

    def test_owner_patch_and_put(self):
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(self.detail, {'title': 'Editado'}, format='json').status_code, 200)
        response = self.client.put(self.detail, {'title': 'Reemplazado', 'content': 'Nuevo texto', 'tags': []}, format='json')
        self.assertEqual(response.status_code, 200)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.title, 'Reemplazado')
        self.assertFalse(self.thread.tags.exists())

    def test_other_user_cannot_modify_or_delete(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.patch(self.detail, {'title': 'No'}, format='json').status_code, 403)
        self.assertEqual(self.client.delete(self.detail).status_code, 403)

    def test_delete_archives_and_preserves_replies(self):
        reply = Reply.objects.create(thread=self.thread, author=self.other, content='Respuesta')
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.delete(self.detail).status_code, 204)
        self.thread.refresh_from_db()
        self.assertTrue(self.thread.is_deleted)
        self.assertTrue(Reply.objects.filter(pk=reply.pk).exists())
        self.assertEqual(self.client.get(self.detail).status_code, 404)

    def test_hidden_and_merged_threads_are_excluded(self):
        Thread.objects.create(author=self.owner, title='Eliminado', content='x', is_deleted=True)
        merged = Thread.objects.create(author=self.owner, title='Fusionado', content='x', merged_into=self.thread)
        self.assertEqual(self.client.get(self.url).data['count'], 1)
        self.assertEqual(self.client.get(reverse('api:thread-detail', args=[merged.pk])).status_code, 404)

    @override_settings(FORUM_BLOCKED_WORDS=['spamdemostracion'])
    def test_invalid_content_and_tags(self):
        self.client.force_authenticate(self.owner)
        for data in [{'title': '', 'content': 'x'}, {'title': 'x', 'content': ' '},
                     {'title': 'x', 'content': 'spamdemostracion'},
                     {'title': 'spamdemostracion', 'content': 'x'},
                     {'title': 'x', 'content': 'x', 'tags': [99999]}]:
            with self.subTest(data=data):
                self.assertEqual(self.client.post(self.url, data, format='json').status_code, 400)
        self.assertEqual(self.client.patch(self.detail, {'content': 'spamdemostracion'}, format='json').status_code, 400)

    def test_suspended_user_can_read_but_cannot_write_or_vote(self):
        self.owner.suspended_until = timezone.now() + timedelta(days=1)
        self.owner.save()
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.post(self.url, {'title': 'x', 'content': 'x'}, format='json').status_code, 403)
        self.assertEqual(self.client.patch(self.detail, {'title': 'x'}, format='json').status_code, 403)
        self.assertEqual(self.client.delete(self.detail).status_code, 403)
        self.assertEqual(self.client.post(self.vote, {'value': 1}, format='json').status_code, 403)

    def test_vote_updates_and_zero_removes(self):
        self.client.force_authenticate(self.other)
        for value in [1, 1, -1, 0]:
            response = self.client.post(self.vote, {'value': value}, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, {'score': value, 'user_vote': value})
            self.assertEqual(ThreadVote.objects.filter(thread=self.thread).count(), int(value != 0))
        self.assertEqual(self.client.post(self.vote, {'value': 2}, format='json').status_code, 400)
        self.assertEqual(self.client.post(self.vote, {}, format='json').status_code, 400)
        self.assertEqual(self.client.get(self.vote).status_code, 405)

    def test_votes_are_private_and_hide_deleted_threads(self):
        ThreadVote.objects.create(thread=self.thread, user=self.owner, value=-1)
        ThreadVote.objects.create(thread=self.thread, user=self.other, value=1)
        votes_url = reverse('api:vote-list')
        self.assertEqual(self.client.get(votes_url).status_code, 403)
        self.client.force_authenticate(self.other)
        response = self.client.get(votes_url)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['value'], 1)
        self.assertEqual(response.data['results'][0]['thread']['puntuacion'], 0)
        hidden_vote = ThreadVote.objects.get(user=self.owner)
        self.assertEqual(self.client.get(reverse('api:vote-detail', args=[hidden_vote.pk])).status_code, 404)
        self.thread.is_deleted = True
        self.thread.save()
        self.assertEqual(self.client.get(votes_url).data['count'], 0)

    def test_search_filters_and_ordering(self):
        second = Thread.objects.create(author=self.other, title='Python', content='Otro', views_count=10)
        ThreadVote.objects.create(thread=self.thread, user=self.other, value=1)
        for query in [{'search': 'Django'}, {'tag': 'django'}, {'author': 'ana'},
                      {'min_votes': 1}, {'max_views': 0}, {'min_views': 0, 'max_votes': 0}]:
            with self.subTest(query=query):
                self.assertEqual(self.client.get(self.url, query).data['count'], 1)
        self.assertEqual(self.client.get(self.url, {'ordering': '-views_count'}).data['results'][0]['id'], second.pk)
        reply = Reply.objects.create(thread=self.thread, author=self.other, content='Solución')
        self.thread.accepted_reply = reply
        self.thread.save()
        self.assertEqual(self.client.get(self.url, {'resolved': 'true'}).data['count'], 1)
        self.assertEqual(self.client.get(self.url, {'min_views': 'abc'}).status_code, 400)

    def test_pagination(self):
        Thread.objects.bulk_create([Thread(author=self.owner, title=f'Hilo {i}', content='x') for i in range(13)])
        response = self.client.get(self.url)
        self.assertEqual(response.data['count'], 14)
        self.assertEqual(len(response.data['results']), 12)
        self.assertIsNotNone(response.data['next'])
        self.assertEqual(len(self.client.get(self.url, {'page': 2}).data['results']), 2)

    def test_tags_read_only(self):
        self.assertEqual(self.client.get(reverse('api:tag-list')).status_code, 200)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.post(reverse('api:tag-list'), {'name': 'nuevo'}).status_code, 405)
        self.assertEqual(self.client.delete(reverse('api:tag-detail', args=[self.tag.pk])).status_code, 405)

    def test_mine_similar_popular_and_stats(self):
        second = Thread.objects.create(author=self.other, title='Relacionado', content='x')
        second.tags.add(self.tag)
        self.assertEqual(self.client.get(reverse('api:thread-mine')).status_code, 403)
        self.client.force_authenticate(self.owner)
        mine = self.client.get(reverse('api:thread-mine'))
        self.assertEqual([x['id'] for x in mine.data['results']], [self.thread.pk])
        similar = self.client.get(reverse('api:thread-similar', args=[self.thread.pk]))
        self.assertEqual([x['id'] for x in similar.data['results']], [second.pk])
        ThreadVote.objects.create(thread=self.thread, user=self.other, value=1)
        popular = self.client.get(reverse('api:popular-threads'))
        self.assertEqual(popular.data['results'][0]['id'], self.thread.pk)
        self.assertEqual(self.client.get(reverse('api:stats')).data['total'], 2)
        self.assertEqual(self.client.get(reverse('api:hello')).data['message'], 'Forum Tech API v1')

    def test_session_login_and_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username='ana', password='Test-1234'))
        self.assertEqual(client.post(self.url, {'title': 'x', 'content': 'x'}, format='json').status_code, 403)
        client.get('/api/auth/login/')
        token = client.cookies['csrftoken'].value
        response = client.post(self.url, {'title': 'x', 'content': 'x'}, format='json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 201)

    def test_documentation(self):
        for url in ['/api/v1/', '/api/schema/', '/api/docs/', '/api/redoc/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_create_and_update_return_complete_current_statistics(self):
        self.client.force_authenticate(self.owner)
        created = self.client.post(self.url, {'title': 'Nuevo', 'content': 'Texto'}, format='json')
        self.assertEqual(created.status_code, 201)
        self.assertEqual(
            {key: created.data.get(key) for key in ['puntuacion', 'num_respuestas', 'esta_resuelto']},
            {'puntuacion': 0, 'num_respuestas': 0, 'esta_resuelto': False},
        )
        ThreadVote.objects.create(thread=self.thread, user=self.other, value=1)
        reply = Reply.objects.create(thread=self.thread, author=self.other, content='Solución')
        self.thread.accepted_reply = reply
        self.thread.save()
        updated = self.client.patch(self.detail, {'title': 'Editado'}, format='json')
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(
            {key: updated.data.get(key) for key in ['puntuacion', 'num_respuestas', 'esta_resuelto']},
            {'puntuacion': 1, 'num_respuestas': 1, 'esta_resuelto': True},
        )

    def test_vote_form_exposes_value_instead_of_thread_fields(self):
        self.client.force_authenticate(self.other)
        response = self.client.options(self.vote)
        self.assertEqual(response.status_code, 200)
        fields = response.data['actions']['POST']
        self.assertEqual(set(fields), {'value'})
        self.assertEqual([choice['value'] for choice in fields['value']['choices']], [-1, 0, 1])

    def test_popular_top_twenty_pagination_excludes_hidden_threads(self):
        Thread.objects.bulk_create([
            Thread(author=self.owner, title=f'Popular {n}', content='x', views_count=n)
            for n in range(25)
        ])
        for fields in ({'is_deleted': True}, {'merged_into': self.thread}):
            Thread.objects.create(author=self.owner, title='Oculto', content='x', views_count=1000, **fields)
        url = reverse('api:popular-threads')
        first = self.client.get(url)
        second = self.client.get(url, {'page': 2})
        self.assertEqual(first.data['count'], 20)
        self.assertEqual(len(first.data['results']), 12)
        self.assertEqual(len(second.data['results']), 8)
        results = first.data['results'] + second.data['results']
        self.assertEqual([row['views_count'] for row in results], list(range(24, 4, -1)))

    def test_similar_paginated_without_duplicates_and_mine_stays_private(self):
        extra_tag = Tag.objects.create(name='python')
        self.thread.tags.add(extra_tag)
        for n in range(14):
            thread = Thread.objects.create(author=self.other, title=f'Similar {n}', content='x')
            thread.tags.set([self.tag, extra_tag])
        hidden = Thread.objects.create(author=self.owner, title='Oculto', content='x', is_deleted=True)
        hidden.tags.add(self.tag)
        url = reverse('api:thread-similar', args=[self.thread.pk])
        first = self.client.get(url)
        second = self.client.get(url, {'page': 2})
        self.assertEqual(first.data['count'], 14)
        ids = [row['id'] for row in first.data['results'] + second.data['results']]
        self.assertEqual(len(set(ids)), 14)
        self.assertNotIn(self.thread.pk, ids)
        self.assertNotIn(hidden.pk, ids)
        self.client.force_authenticate(self.owner)
        mine = self.client.get(reverse('api:thread-mine'), {'author': self.other.username})
        self.assertEqual(mine.data['count'], 0)
