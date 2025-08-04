from django.db import models

class Activation_btn(models.Model):
    status = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.status}"