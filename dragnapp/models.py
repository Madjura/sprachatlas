from django.db import models


# Create your models here.
from django.db.models import Q


class IndexRelationManager(models.Manager):
    def for_alias(self, alias):
        return self.filter(alias=alias).select_related("paragraph", "alias", "paragraph__text")

    def all_relations_for_term(self, alias, term):
        return self.filter(Q(alias=alias) & (Q(subject=term) | Q(object=term))).select_related("paragraph", "alias", "paragraph__text")

    def all_provs_for_triple(self, alias, s, p, o):
        return self.filter(alias=alias, subject=s, predicate=p, object=o).values_list("paragraph", "value")


class KbRelationManager(models.Manager):
    def for_alias(self, alias, related_to=False, all_relations=False):
        if all_relations:
            return self.filter(alias=alias).select_related("paragraph", "alias", "paragraph__text")
        if related_to:
            return self.filter(alias=alias, predicate="related to").select_related("paragraph", "alias", "paragraph__text")
        else:
            return self.filter(alias=alias, predicate="close to").select_related("paragraph", "alias", "paragraph__text")


class ClosenessManager(models.Manager):
    def for_alias(self, alias):
        return self.filter(paragraph__text__in=alias.texts.all()).select_related("paragraph", "paragraph__text")


class Text(models.Model):
    name = models.TextField(unique=True)
    path = models.TextField()
    paragraphs = models.IntegerField(null=True)

    def __str__(self):
        return self.name


class Paragraph(models.Model):
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    position = models.IntegerField()
    content = models.TextField()

    def __str__(self):
        return f"(Model): {self.text}: Paragraph {self.position}"

    class Meta:
        unique_together = [("text", "position"), ]


class Closeness(models.Model):
    paragraph = models.ForeignKey(Paragraph, on_delete=models.CASCADE)
    token1 = models.TextField()
    token2 = models.TextField()
    closeness = models.FloatField()

    objects = ClosenessManager()

    class Meta:
        unique_together = [("paragraph", "token1", "token2"), ]


class Alias(models.Model):
    identifier = models.TextField(unique=True)
    texts = models.ManyToManyField(Text)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return self.identifier


class LexiconEntry(models.Model):
    alias = models.ForeignKey(Alias, on_delete=models.CASCADE)
    token = models.TextField()
    frequency = models.PositiveIntegerField()

    class Meta:
        unique_together = [("alias", "token"), ]


class KbRelation(models.Model):
    subject = models.TextField()
    predicate = models.TextField()
    object = models.TextField()
    alias = models.ForeignKey(Alias, on_delete=models.CASCADE)
    paragraph = models.ForeignKey(Paragraph, on_delete=models.CASCADE, null=True)
    value = models.FloatField(null=True)

    objects = KbRelationManager()

    def get_value_triple(self, paragraph=False):
        if paragraph:
            return self.subject, self.predicate, self.object, self.value, self.paragraph
        return self.subject, self.predicate, self.object, self.value

    def __str__(self):
        return f"{self.subject} {self.predicate} {self.object}: {self.value}, {self.paragraph}"

    class Meta:
        unique_together = [("subject", "predicate", "object", "alias", "paragraph"), ]


class IndexRelation(models.Model):
    alias = models.ForeignKey(Alias, on_delete=models.CASCADE)
    subject = models.TextField()
    predicate = models.TextField()
    object = models.TextField()
    value = models.FloatField()
    paragraph = models.ForeignKey(Paragraph, on_delete=models.CASCADE, null=True)

    objects = IndexRelationManager()

    def get_value_triple(self, paragraph=False):
        if paragraph:
            return self.subject, self.predicate, self.object, self.value, self.paragraph
        return self.subject, self.predicate, self.object, self.value

    def __str__(self):
        return f"{self.subject} {self.predicate} {self.object}: {self.value}, {self.paragraph}"

    class Meta:
        unique_together = [("alias", "subject", "predicate", "object", "value", "paragraph"), ]
