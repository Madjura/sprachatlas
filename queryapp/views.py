# -*- coding: utf-8 -*-
"""Views for the queryapp. Responsible for handling all user interactions regarding queries."""
import os
import re

from celery.bin.control import inspect
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import FormView, ListView

from allsteps.allsteps import all_steps
from dataapp.models import InverseIndex
from sprachatlas import settings
from dragnapp.models import Alias, Paragraph
from levenshtein.levenhstein import find_candidates_from_db
from query import querystep
from queryapp.forms import QueryForm, ProcessForm, TaskStatusForm, SuggestForm, QueryFormDb
from queryapp.models import Text, TextsAlias
from statusapp.models import ProcessStatus
from util import paths


def query_db(request):
    context = {}
    if request.method == "POST":
        queryform = QueryFormDb(request.POST)
        # check if form has not been tampered with
        if queryform.is_valid():
            # get corresponding alias to know which texts are being queried
            alias = Alias.objects.get(pk=queryform.cleaned_data["texts"])
            # check if edges between non-query nodes are to be considered
            lesser_edges = queryform.cleaned_data["lesser_edges"]
            # perform the calculation of the query
            result = querystep.query_db(queryform.cleaned_data["query"], alias=alias, lesser_edges=lesser_edges)
            # generate the result graph
            graph = result.generate_statement_graph_db(
                queryform.cleaned_data["max_nodes"], queryform.cleaned_data["max_edges"], alias)
            # get the content of the found paragraphs
            samples = load_and_prepare_provenance(
                result.get_top_provenances(queryform.cleaned_data["top_text_samples"]), alias=alias)
            # get names/labels of the nodes in the result graph
            nodes = [x.name for x in graph.nodes]
            # generate stuff for display in the template
            samples = markup_samples(samples, nodes)
            context = {
                "graph_elements": graph.to_json(),
                "queryform": queryform,
                "samples": samples,
                "alias": alias.identifier,
                "suggestform": SuggestForm(),
            }
        return render(request, "queryapp/result.html", context)
    elif request.method == "GET":
        # display empty form to the user
        queryform = QueryFormDb()
        context = {
            "queryform": queryform,
            "suggestform": SuggestForm(),
        }
        return render(request, "queryapp/result.html", context)


def query(request):
    """
    View for a simple user query.

    :param request: A Django request object.
    :return: A rendered page showing the result of the query.
    """
    context = {}
    if request.method == "POST":
        queryform = QueryForm(request.POST)
        # check if form has not been tampered with
        if queryform.is_valid():
            # get corresponding alias to know which texts are being queried
            alias = TextsAlias.objects.get(pk=queryform.cleaned_data["texts"])
            # check if edges between non-query nodes are to be considered
            lesser_edges = queryform.cleaned_data["lesser_edges"]
            # perform the calculation of the query
            result = querystep.query(queryform.cleaned_data["query"], alias=alias.identifier,
                                     lesser_edges=lesser_edges)
            # generate the result graph
            graph = result.generate_statement_graph(queryform.cleaned_data["max_nodes"],
                                                    queryform.cleaned_data["max_edges"])
            # get the content of the found paragraphs
            samples = load_and_prepare_provenance_db(
                result.get_top_provenances(queryform.cleaned_data["top_text_samples"]), alias=alias)
            # get names/labels of the nodes in the result graph
            nodes = [x.name for x in graph.nodes]
            # generate stuff for display in the template
            samples = markup_samples(samples, nodes)
            context = {
                "graph_elements": graph.to_json(),
                "queryform": queryform,
                "samples": samples,
                "alias": alias.identifier,
                "suggestform": SuggestForm(),
            }
        return render(request, "queryapp/result.html", context)
    elif request.method == "GET":
        # display empty form to the user
        queryform = QueryForm()
        context = {
            "queryform": queryform,
            "suggestform": SuggestForm(),
        }
        return render(request, "queryapp/result.html", context)


def load_and_prepare_provenance(tops, alias):
    """
    Loads provenances and generates a list of tuples of name, score and content of those provenances.

    :param tops: The provenances/paragraphs being loaded.
    :param alias: The Alias of the queried texts.
    :return: A list of tuples of name, score and content of the provenances.
    """
    texts = []
    for paragraph_id, score in tops:
        paragraph = Paragraph.objects.get(pk=paragraph_id)
        texts.append((f"{paragraph.text.name}_{paragraph.position}", score, paragraph.content))
    return texts


def load_and_prepare_provenance_db(tops, alias):
    """
    Loads provenances and generates a list of tuples of name, score and content of those provenances.

    :param tops: The provenances/paragraphs being loaded.
    :param alias: The Alias of the queried texts.
    :return: A list of tuples of name, score and content of the provenances.
    """
    texts = []
    alias = alias.identifier
    for name, score in tops:
        with open(os.path.join(paths.PARAGRAPH_CONTENT_PATH, alias, name), "r", encoding="utf8") as text:
            texts.append((name, score, text.read()))
    return texts


def markup_samples(samples, nodes):
    """
    Processes the content of the found provenances; emboldens words that appear in the graph.

    :param samples: The provenances with their name, score and content.
    :param nodes: The label/name of the nodes in the graph.
    :return: A list containing tuples in the format (name, score, content, contained words) of the provenances.
    """
    normalized = set()
    for node in nodes:
        normalized |= {(node.replace("_", " "), node)}
    updated_samples = []
    normalized = sorted(list(normalized), key=lambda x: len(x[0]), reverse=True)
    for name, score, content in samples:
        matches = set()
        for n, original in normalized:
            match = (re.findall("\\b{}\\b".format(re.escape(n)), content, re.IGNORECASE), original)
            markup_check = match[0]
            if markup_check:
                markup_check = markup_check[0]  # non-empty list
                (match, original) = match
                fixed_regex = "\\b{}\\b".format(re.escape(markup_check))
                content = re.sub(fixed_regex, "<b>{}</b>".format(re.escape(markup_check)), content, flags=re.IGNORECASE)
                if markup_check.lower() == original.lower():
                    original = ""
                matches |= {(markup_check, original)}
        updated_samples.append((name, score, content, matches))
    return updated_samples


def process(request):
    """
    View to process a text or multiple with the pipeline.
    Note that this can take very long to finish, depending on the total size of the text(s).

    :param request: A Django request object.
    :return: A rendered view showing the texts that were processed.
    """
    texts = []
    context = {}
    form = TaskStatusForm()
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
                    text_objects.append(Text.objects.create(name=text))
                except IntegrityError:
                    text_objects.append(Text.objects.get(name=text))
            # get alias if exists
            alias = TextsAlias.for_texts(text_objects)
            if not alias:
                # if it doesnt exist, create it
                name_alias = ",".join(texts)
                alias = TextsAlias.objects.create(identifier=name_alias)
                alias.save()
                for text in text_objects:
                    alias.texts.add(text)
            # perform all steps in the pipeline
            if settings.USE_CELERY:
                from .tasks import all_steps_task
                # get alias object here
                alias_object = alias
                alias = alias.identifier
                task_id = all_steps_task.delay(processform.cleaned_data["texts"], processform.cleaned_data["language"],
                                               alias)
                process_status = ProcessStatus(task_id=task_id, alias=alias_object)
                process_status.save()
                context["task"] = task_id
            else:
                print("NO CELERY")
                all_steps(processform.cleaned_data["texts"], language=processform.cleaned_data["language"], alias=alias)
    processform = ProcessForm(text_choices=texts)
    context["processform"] = processform
    context["statusform"] = form
    return render(request, "queryapp/process.html", context)


def get_provenance(request):
    """
    View to display the contents of a certain paragraph.
    Used by the Distant Reader to show previous or next paragraphs.

    :param request: A Django request object.
    :return: The contents of the selected (previous or next) paragraph in JSON format.
    """
    provenance = request.POST["provenance"]
    next_or_previous = provenance.split("_")[-1]
    # get the id of the paragraph to find the next or previous one
    provenance_id = int(re.findall(r'_\d+_', provenance)[0].split("_")[1])
    if next_or_previous == "next":
        provenance_id += 1
    elif next_or_previous == "previous":
        provenance_id -= 1
    # get the name
    provenance_name = re.findall('(.+)_\d+', provenance)[0]
    # needed for the links of previous/next for the paragraph thats going to be displayed
    provenance_id_next = provenance_id
    provenance_id_previous = provenance_id
    provenance_next = "{}_{}".format(provenance_name, provenance_id_next)
    provenance_previous = "{}_{}".format(provenance_name, provenance_id_previous)
    alias = request.POST["alias"]
    matches = request.POST.getlist("matches[]")
    file_path = os.path.join(paths.PARAGRAPH_CONTENT_PATH, alias, provenance_name + "_" + str(provenance_id))
    # file_path = "{}/{}/{}_{}".format(paths.PARAGRAPH_CONTENT_PATH, alias, provenance_name, provenance_id)
    data = {}
    if os.path.isfile(file_path):
        with open(file_path, "r", encoding="utf8") as paragraph:
            content = paragraph.read()
            # mark up the words that appear in the result graph by making them bold
            for n in matches:
                match = re.findall("\\b{}\\b".format(re.escape(n)), content, re.IGNORECASE)
                if match:
                    content = re.sub("\\b{}\\b".format(re.escape(n)), "<b>{}</b>".format(match[0]), content, flags=re.IGNORECASE)
            data["content"] = content
    data["provenance"] = provenance
    data["next"] = provenance_next
    data["previous"] = provenance_previous
    data["matches"] = ";".join(matches)
    return JsonResponse(data)


def check_all_steps_task_status(request):
    """
    View to check the status of a task running on/with Celery.
    :param request:
    :return:
    """
    context = {}
    if request.method == "POST":
        form = TaskStatusForm(request.POST)
        if form.is_valid():
            task = form.cleaned_data["task"]
            from celery.result import AsyncResult
            from .tasks import all_steps_task
            result = AsyncResult(id=task, app=all_steps_task)
            context["task"] = task
            context["statusform"] = form
            context["state"] = result.state
        else:
            print("NOT VALID")
            print(form.errors)
    return render(request, "queryapp/process.html", context)


def suggest_view(request):
    if request.method == "POST":
        suggestform = SuggestForm(request.POST)
        if suggestform.is_valid():
            texts = TextsAlias.objects.get(pk=suggestform.cleaned_data["texts"]).identifier
            suggestions = find_candidates_from_db(suggestform.cleaned_data["word"], suggestform.cleaned_data["limit"],
                                                  texts)
            return render(request, "queryapp/levenshtein.html", {"suggestions": suggestions})
    return redirect("query")


def frequency_view(request, pk=None):
    context = {}
    if not pk:
        aliases = TextsAlias.objects.all()
        context["aliases"] = aliases
    else:
        alias = TextsAlias.objects.get(pk=pk)
        texts = alias.texts
        index_Q = Q()
        for text in texts.all():
            index_Q |= Q(index__icontains=text)
        indices = InverseIndex.objects.values("term").annotate(Count("id")).order_by().filter(index_Q)
        counts = []
        for index in indices:
            counts.append((index["id__count"], index["term"]))
        counts = sorted(counts, key=lambda x: x[0], reverse=True)
        context["counts"] = counts
        context["alias"] = alias.identifier
    return render(request, "queryapp/frequencies.html", context)

if __name__ == "__main__":
    markup_samples(["Harry visited Hagrid and Harry."], ["harry_and_ron", "ron"])
