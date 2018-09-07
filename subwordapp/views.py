import os
from collections import defaultdict

from django.db import IntegrityError
from django.shortcuts import render


# Create your views here.
from queryapp.forms import ProcessForm
from queryapp.views import query
from subword.io_util import load_graph
from subword.similarity import vector_similarities_compare, vector_similarities_text
from subword.subword_main import create_vectorspace_and_word_vectors_texts
from subwordapp.forms import SimilarityForm, BigramGraphForm
from subwordapp.models import SubwordText, SubwordAlias
from util import paths


def bigrams(request):
    processed = os.listdir(paths.SUBWORD_MODEL_PATH)
    context = {}
    if request.method == "POST":
        bigramgraphform = BigramGraphForm(text_choices=processed, data=request.POST)
        context["bigramform"] = bigramgraphform
        if bigramgraphform.is_valid():
            texts = bigramgraphform.cleaned_data["texts"]
            readable = bigramgraphform.cleaned_data["readable"]
            alias = SubwordAlias.objects.get(identifier=texts[0])
            graph = load_graph(alias, readable=readable)
            context["graph_elements"] = graph
            return render(request, "subwordapp/bigrams.html", context)
    elif request.method == "GET":
        context["bigramform"] = BigramGraphForm(text_choices=processed)
        return render(request, "subwordapp/bigrams.html", context)


def process_subwords(request):
    texts = []
    context = {}
    for file in os.listdir(paths.TEXT_PATH):
        if os.path.isfile(os.path.join(paths.TEXT_PATH, file)):
            texts.append(file)
    if request.method == "POST":
        processform = ProcessForm(text_choices=texts, data=request.POST)
        # check if form is valid and has not been tampered with
        if processform.is_valid():
            text_objects = []
            texts = processform.cleaned_data["texts"]
            for text in texts:
                try:
                    text_objects.append(SubwordText.objects.create(name=text))
                except IntegrityError:
                    text_objects.append(SubwordText.objects.get(name=text))
            # get alias if exists
            alias = SubwordAlias.for_texts(text_objects)
            if not alias:
                # if it doesnt exist, create it
                name_alias = ",".join(texts)
                alias = SubwordAlias.objects.create(identifier=name_alias)
                alias.save()
                for text in text_objects:
                    alias.texts.add(text)
            create_vectorspace_and_word_vectors_texts(alias)
            return query(request)
    elif request.method == "GET":
        context["processform"] = ProcessForm(text_choices=texts)
        return render(request, "subwordapp/subword_process.html", context)


def _sim_alphabetical(sim, compare=False):
    alphabetical = defaultdict(lambda: defaultdict(lambda: None))
    for k, v in sim.items():
        if compare:
            alphabetical[k[0]][k] = list(v)
        else:
            vals = sorted(list(v.items()), key=lambda j: j[1], reverse=True)
            alphabetical[k[0]][k] = vals
    t = []
    for k, v in alphabetical.items():
        if compare:
            t.append((k, v))
        else:
            tt = []
            for kk, vv in v.items():
                tt.append((kk, vv))
            tt = sorted(tt, key=lambda j: j[1])
            t.append((k, tt))
    return sorted(t, key=lambda k: k[0])


def similarity(request):
    context = {"comparetwo": False}
    processed = os.listdir(paths.SUBWORD_MODEL_PATH)
    if request.method == "POST":
        similarityform = SimilarityForm(text_choices=processed, data=request.POST)
        context["similarityform"] = similarityform
        if similarityform.is_valid():
            texts = similarityform.cleaned_data["texts"]
            if len(texts) > 2:
                context["error"] = "Only maximum of two aliases are eligible for comparison."
                return render(request, "subwordapp/similarity.html", context)
            elif len(texts) == 2:
                context["comparetwo"] = True
                alias1 = SubwordAlias.objects.get(identifier=texts[0])
                alias2 = SubwordAlias.objects.get(identifier=texts[1])
                cosines = vector_similarities_compare(alias1, alias2)
                cosines = _sim_alphabetical(cosines, compare=True)
                context["cosines"] = cosines
                return render(request, "subwordapp/similarity.html", context)
            else:
                alias = SubwordAlias.objects.get(identifier=texts[0])
                cosines = vector_similarities_text(alias)
                cosines = _sim_alphabetical(cosines)
                context["cosines"] = cosines
                return render(request, "subwordapp/similarity.html", context)
    elif request.method == "GET":
        context["similarityform"] = SimilarityForm(text_choices=processed)
        return render(request, "subwordapp/similarity.html", context)