from django.db import models
from django.db.models import Count


class SubwordText(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class SubwordAlias(models.Model):
    identifier = models.CharField(max_length=100, unique=True)
    texts = models.ManyToManyField(SubwordText)
    processed = models.BooleanField(default=False)

    @staticmethod
    def for_texts(texts):
        result = SubwordAlias.objects.filter(texts__in=texts).annotate(num_texts=Count("texts")) \
            .filter(num_texts=len(texts))
        for r in result:
            if len(r.identifier.split(",")) == len(texts):
                return r