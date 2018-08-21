from django.shortcuts import render


# Create your views here.
def bigrams(request):
    with open("E:\PycharmProjects\sprachatlas\subword\\test_graph.json", "r") as f:
        graph = f.read()
    return render(request, "subwordapp/bigrams.html", {"graph_elements": graph})
