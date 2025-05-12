from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from chat.models import ChatRequest

User = get_user_model()

class ChatRequestFlowTest(TestCase):
    def setUp(self):
        self.elder = User.objects.create_user(username='elder', password='elderpass', role='elderly')
        self.caregiver = User.objects.create_user(username='caregiver', password='caregiverpass', role='caregiver', is_verified=True)

    def test_send_and_respond_request(self):
        self.client.login(username='elder', password='elderpass')
        # Elder sends request
        resp = self.client.get(reverse('chat:send_request', args=[self.caregiver.id]))
        self.assertEqual(ChatRequest.objects.count(), 1)
        chat_request = ChatRequest.objects.first()
        self.assertEqual(chat_request.status, 'pending')

        # Caregiver sees the request
        self.client.logout()
        self.client.login(username='caregiver', password='caregiverpass')
        resp = self.client.get(reverse('chat:request_list'))
        self.assertContains(resp, 'Pending')

        # Caregiver accepts the request
        resp = self.client.get(reverse('chat:respond_request', args=[chat_request.id, 'accepted']))
        chat_request.refresh_from_db()
        self.assertEqual(chat_request.status, 'accepted')