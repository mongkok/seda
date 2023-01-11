from django.test import TestCase
from django.urls import reverse


class ViewsTests(TestCase):
    def test_myview(self):
        response = self.client.get(reverse("myapp:myview"))
        self.assertEqual(response.status_code, 200)
