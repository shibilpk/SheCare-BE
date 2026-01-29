from django.db import models


class WeightUnisChoices(models.TextChoices):
    KG = "kg", "KG"
    LB = "lb", "LB"
