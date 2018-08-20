function browserTarget(e) {
    var target = e.cyTarget;
    if (!target) {
        target = e.target;
    }
    return target;
}

var provenancesScroll = [];
var headingScroll = [];
var lastScroll = -1;
var lastHeadingScroll = -1;

function updateCy(elements) {
    var cy = cytoscape({
        container: $("#cy"),
        boxSelectionEnabled: true,
        zoomingEnabled: true,
        userZoomingEnabled: true,
        style: [
            {
                selector: 'node',
                style: {
                    //"content": "data(id)",
                    "font-size": 20,
                    "text-halign": "center",
                    "text-valign": "top",
                    "width": "data(size)",
                    "height": "data(size)",
                    "background-color": "data(color)",
                }
            },
            {
                selector: "edge",
                style: {
                    "line-color": "data(color)",
                    'curve-style': 'bezier',
                    "arrow-scale": 5,
                    "width": 2,
                    "target-arrow-color": "black",
                    'target-arrow-shape': 'triangle' // there are far more options for this property here: http://js.cytoscape.org/#style/edge-arrow
                }
            },
            {
                selector: ".hidden",
                style: {
                    "visibility": "hidden"
                }
            }
        ]
    });
    var options = {
        name: 'spread',
        animate: true, // whether to show the layout as it's running
        ready: undefined, // Callback on layoutready
        stop: undefined, // Callback on layoutstop
        fit: false, // Reset viewport to fit default simulationBounds
        minDist: 100, // Minimum distance between nodes
        padding: 20, // Padding
        expandingFactor: -1.0, // If the network does not satisfy the minDist
        // criterium then it expands the network of this amount
        // If it is set to -1.0 the amount of expansion is automatically
        // calculated based on the minDist, the aspect ratio and the
        // number of nodes
        maxFruchtermanReingoldIterations: 50, // Maximum number of initial force-directed iterations
        maxExpandIterations: 4, // Maximum number of expanding iterations
        boundingBox: undefined, // Constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
        randomize: false // uses random initial node positions on true
    };
    if (elements) {
        cy.add(elements);
    } else {
        cy.add(graphElements);
    }
    var layout = cy.elements().layout(options);
    try {
        layout.run();
    } catch (err) {
    }
    cy.nodes().on("tap", function (e) {
        // this check is needed for cross browser compability
        var target = browserTarget(e);
        var connectedNodes = target.closedNeighborhood().nodes();
        connectedNodes
            .selectify()
            .select()
            .unselectify()
    });
    cy.on("tap", function (e) {
        var target = browserTarget(e);
        if (target == cy) {
            cy.nodes()
                .selectify()
                .unselect()
                .unselectify()
            ;
        }
    });
    // prov showing
    cy.edges().on("taphold", function(e) {
        var edge = browserTarget(e);
        var color = edge.data("color");
        var provs = edge.data("provs");
        var provNodes = [];
        provNodes.push({
                group: "nodes",
                data: {
                    "id": "PROVPARENT",
                    "font-size": 20,
                    "size": 30,
                    "width": 30,
                    "color": "#D3D3B5",
                    "background-opacity": 10000,
                    "background-blacken": -1,
                },
                position: {
                    "x": i,
                    "y": i
                },
                grabbable: true,
                classes: "prov-nodes"
            }
        )
        for (var i = 0; i < provs.length; i++) {
            var prov = provs[i];
            provNodes.push({
                group: "nodes",
                data: {
                    "id": prov,
                    "font-size": 20,
                    "size": 30,
                    "width": 30,
                    "color": "yellow",
                    "parent": "PROVPARENT"
                },
                position: {
                    "x": i,
                    "y": i
                },
                grabbable: true,
                classes: "prov-nodes provlink",
                style: {
                    "shape": "vee",
                    "content": prov
                }
            });
        }
        var targetNode = edge.target().attr("id");
        var sourceNode = edge.source().attr("id");
        provNodes.push({
                group: "nodes",
                data: {
                    "id": "PROVCONNECTOR",
                    "font-size": 20,
                    "size": 30,
                    "width": 30,
                    "color": color,
                },
                position: {
                    "x": i,
                    "y": i
                },
                grabbable: true,
                classes: "prov-nodes",
                style: {
                    "shape": "heptagon",
                    "content": ""
                }
        });
        provNodes.push({
            group: "edges",
            data: {
                "id": "PROVCONNECTOR-SOURCE",
                "source": sourceNode,
                "target": "PROVCONNECTOR",
                "color": color,
            },
            style: {
                "color": "black",
                "curve-style": "haystack",
                "font-size": 20,
                "text-valign": "bottom",
                "text-halign": "right"
            },
            classes: "prov-nodes"
        });
        provNodes.push({
            group: "edges",
            data: {
                "id": "PROVCONNECTOR-TARGET",
                "source": targetNode,
                "target": "PROVCONNECTOR",
                "color": color,
            },
            style: {
                "color": "black",
                "curve-style": "haystack",
                "font-size": 20,
                "text-valign": "bottom",
                "text-halign": "right"
            },
            classes: "prov-nodes"
        });
        provNodes.push({
            group: "edges",
            data: {
                "id": "PROVCONNECTOR-LINK",
                "source": "PROVCONNECTOR",
                "target": "PROVPARENT",
                "color": color,
            },
            style: {
                "color": "black",
                "curve-style": "haystack",
                "font-size": 20,
                "text-valign": "bottom",
                "text-halign": "right"
            },
            classes: "prov-nodes"
        });
        cy.$(".prov-nodes").remove();
        cy.add(provNodes);
        var provLinkNodes = cy.$(".provlink");
        for (var i = 0; i < provLinkNodes.length; i++) {
            var provLinkNode = provLinkNodes[i];
            provLinkNode.on("taphold", function (event) {
                var target = browserTarget(event);
                var heading = $("[id='" + target.id() + "']");
                if (heading.length) {
                    var wrapper = heading.closest(".text-match-wrapper");
                    var position = wrapper.position();
                    $(window).scrollTop(position.top - 90);
                }
            });
            // layoutNodes("spread", cy.nodes());
            layoutNodes("grid", cy.$(".prov-nodes"));
        }
    });
    var menu = {
        // List of initial menu items
        menuItems: [
            {
                id: 'hide-this',
                title: 'Hide this and all connected',
                selector: 'node',
                onClickFunction: function (event) {
                    // get the selected node
                    var target = browserTarget(event);
                    // get all edges connected to this node
                    var edges = target.connectedEdges();
                    var connectedNodes = edges.connectedNodes();
                    target.addClass("hidden");
                    edges.addClass("hidden");
                    edges.connectedNodes().forEach(function (node) {
                        if (node.connectedEdges().filter(":visible").size() == 0) {
                            node.addClass("hidden");
                        }
                    });
                },
                coreAsWell: false,
                disabled: false
            },
            {
                id: "show-only",
                title: "Show only this and directly connected",
                selector: "node",
                onClickFunction: function (event) {
                    var target = browserTarget(event);
                    var edges = target.connectedEdges();
                    var connectedNodes = edges.connectedNodes();
                    cy.collection()
                        .union(target)
                        .union(edges)
                        .union(connectedNodes)
                        .absoluteComplement()
                        .addClass("hidden");
                },
                coreAsWell: false,
            },
            {
                id: "show-all",
                title: "Show all nodes and edges",
                selector: "node, edge",
                onClickFunction: function (event) {
                    cy.nodes().filter(":hidden").removeClass("hidden");
                    cy.edges().filter(":hidden").removeClass("hidden");
                },
                disabled: false,
                coreAsWell: true,
            },
            {
                id: "add-to-query",
                title: "Add this to query",
                selector: "node",
                onClickFunction: function (event) {
                    var target = browserTarget(event);
                    $("#id_query").val($("#id_query").val() + "," + target.data("id"));
                },
                coreAsWell: false,
            },
            {
                id: "show-related-to",
                title: "Show only 'related to' edges",
                selector: "edge, node",
                onClickFunction: function (event) {
                    var edges = cy.edges("[color != 'red'][color != 'magenta']");
                    edges.forEach(function (edge) {
                        edge.addClass("hidden");
                    });
                    cy.nodes().forEach(function (node) {
                        if (node.connectedEdges().filter(":visible").size() == 0) {
                            node.addClass("hidden");
                        }
                    });
                },
                coreAsWell: false,
            },
            {
                id: "show-close-to",
                title: "Show only 'close to' edges",
                selector: "edge, node",
                onClickFunction: function (event) {
                    var edges = cy.edges("[color != 'blue'][color != 'magenta']");
                    edges.forEach(function (edge) {
                        edge.addClass("hidden");
                    });
                    cy.nodes().forEach(function (node) {
                        if (node.connectedEdges().filter(":visible").size() == 0) {
                            node.addClass("hidden");
                        }
                    });
                },
                coreAsWell: false,
            },
            {
                id: "layout-concentric",
                title: "Concentric layout",
                selector: "node",
                onClickFunction: function (event) {
                    var target = browserTarget(event);
                    layoutNodes("concentric", target.closedNeighborhood().nodes());
                },
                coreAsWell: false
            },
            {
                id: "layout-spread",
                title: "Spread layout",
                selector: "node",
                onClickFunction: function (event) {
                    var target = browserTarget(event);
                    layoutNodes("spread", target.closedNeighborhood().nodes());
                },
                coreAsWell: false
            },
            {
                id: "layout-grid",
                title: "Grid layout",
                selector: "node",
                onClickFunction: function (event) {
                    var target = browserTarget(event);
                    layoutNodes("grid", target.closedNeighborhood().nodes());
                },
                coreAsWell: false
            },
            {
                id: "layout-circle",
                title: "Circle layout",
                selector: "node",
                onClickFunction: function (event) {
                    var target = browserTarget(event);
                    layoutNodes("circle", target.closedNeighborhood().nodes());
                },
                coreAsWell: false
            },
            {
                id: "layout-breadthfirst",
                title: "Breadthfirst layout",
                selector: "node",
                onClickFunction: function (event) {
                    var target = browserTarget(event);
                    layoutNodes("breadthfirst", target.closedNeighborhood().nodes());
                },
                coreAsWell: false
            },
            {
                id: "layout-cose",
                title: "Cose layout",
                selector: "node",
                onClickFunction: function (event) {
                    var target = browserTarget(event);
                    layoutNodes("cose", target.closedNeighborhood().nodes());
                },
                coreAsWell: false
            },
            {
                id: "find-samples",
                title: "Find text(s) containing this",
                selector: "node",
                onClickFunction: function (event) {
                    var target = browserTarget(event);
                    $("#sample-scroll").html("Scrolling for: " + target.id());
                    provenancesScroll = [];
                    headingScroll = [];
                    var edges = target.connectedEdges();
                    for (var i = 0; i < edges.length; i++) {
                        var edge = edges[i];
                        var provs = edge.data("provs");
                        for (var j = 0; j < provs.length; j++) {
                            var prov = provs[j];
                            var heading = $("[id='"+prov+"']");
                            if (heading.length) {
                                headingScroll.push(heading);
                            }
                        }
                    }
                    // scroll based on the contains list
                    $(".match-list").each(function() {
                        var flag = false;
                        $(this).children("li").each(function() {
                            var label = $(this).html();
                            var targetLabel = target.id();
                            var targetLabelReplace = target.id().replace(/_/g, " ").toLowerCase();
                            if (target.id().replace(/_/g, " ").toLowerCase() == label.toLowerCase()) {
                                var matchingList = $(this).closest(".match").closest(".text-match-wrapper");
                                var top = matchingList.position().top;
                                console.log(top);
                                flag = true;
                                //$(window).scrollTop( top - 50);
                            }
                        });
                        if (flag) {
                            provenancesScroll.push($(this));
                        }
                    });
                },
                coreAsWell: false
            }
        ],
        // css classes that menu items will have
        menuItemClasses: [
            // add class names to this list
        ],
        // css classes that context menu will have
        contextMenuClasses: [
            // add class names to this list
        ]
    };
    cy.contextMenus(menu);
}

function layoutNodes(option, nodes) {
    var concentric = {
        name: 'concentric',
        fit: true, // whether to fit the viewport to the graph
        padding: 30, // the padding on fit
        startAngle: 3 / 2 * Math.PI, // where nodes start in radians
        sweep: undefined, // how many radians should be between the first and last node (defaults to full circle)
        clockwise: true, // whether the layout should go clockwise (true) or counterclockwise/anticlockwise (false)
        equidistant: false, // whether levels have an equal radial distance betwen them, may cause bounding box overflow
        minNodeSpacing: 10, // min spacing between outside of nodes (used for radius adjustment)
        boundingBox: undefined, // constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
        avoidOverlap: true, // prevents node overlap, may overflow boundingBox if not enough space
        height: undefined, // height of layout area (overrides container height)
        width: undefined, // width of layout area (overrides container width)
        concentric: function (node) { // returns numeric value for each node, placing higher nodes in levels towards the centre
            return node.degree();
        },
        levelWidth: function (nodes) { // the variation of concentric values in each level
            return nodes.maxDegree() / 4;
        },
        animate: false, // whether to transition the node positions
        animationDuration: 500, // duration of animation in ms if enabled
        animationEasing: undefined, // easing of animation if enabled
        ready: undefined, // callback on layoutready
        stop: undefined // callback on layoutstop
    };
    var spread = {
        name: 'spread',
        animate: true, // whether to show the layout as it's running
        ready: undefined, // Callback on layoutready
        stop: undefined, // Callback on layoutstop
        fit: false, // Reset viewport to fit default simulationBounds
        minDist: 100, // Minimum distance between nodes
        padding: 20, // Padding
        expandingFactor: -1.0, // If the network does not satisfy the minDist
        // criterium then it expands the network of this amount
        // If it is set to -1.0 the amount of expansion is automatically
        // calculated based on the minDist, the aspect ratio and the
        // number of nodes
        maxFruchtermanReingoldIterations: 50, // Maximum number of initial force-directed iterations
        maxExpandIterations: 4, // Maximum number of expanding iterations
        boundingBox: undefined, // Constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
        randomize: false // uses random initial node positions on true
    };
    var grid = {
        name: 'grid',
        fit: true, // whether to fit the viewport to the graph
        padding: 30, // padding used on fit
        boundingBox: undefined, // constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
        avoidOverlap: true, // prevents node overlap, may overflow boundingBox if not enough space
        avoidOverlapPadding: 10, // extra spacing around nodes when avoidOverlap: true
        condense: false, // uses all available space on false, uses minimal space on true
        rows: 1, // force num of rows in the grid
        cols: undefined, // force num of columns in the grid
        position: function (node) {
        }, // returns { row, col } for element
        sort: undefined, // a sorting function to order the nodes; e.g. function(a, b){ return a.data('weight') - b.data('weight') }
        animate: false, // whether to transition the node positions
        animationDuration: 500, // duration of animation in ms if enabled
        animationEasing: undefined, // easing of animation if enabled
        ready: undefined, // callback on layoutready
        stop: undefined // callback on layoutstop
    };
    var circle = {
        name: 'circle',
        fit: true, // whether to fit the viewport to the graph
        padding: 30, // the padding on fit
        boundingBox: undefined, // constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
        avoidOverlap: true, // prevents node overlap, may overflow boundingBox and radius if not enough space
        radius: undefined, // the radius of the circle
        startAngle: 3 / 2 * Math.PI, // where nodes start in radians
        sweep: undefined, // how many radians should be between the first and last node (defaults to full circle)
        clockwise: true, // whether the layout should go clockwise (true) or counterclockwise/anticlockwise (false)
        sort: undefined, // a sorting function to order the nodes; e.g. function(a, b){ return a.data('weight') - b.data('weight') }
        animate: false, // whether to transition the node positions
        animationDuration: 500, // duration of animation in ms if enabled
        animationEasing: undefined, // easing of animation if enabled
        ready: undefined, // callback on layoutready
        stop: undefined // callback on layoutstop
    };
    var breadthfirst = {
        name: 'breadthfirst',
        fit: true, // whether to fit the viewport to the graph
        directed: false, // whether the tree is directed downwards (or edges can point in any direction if false)
        padding: 30, // padding on fit
        circle: false, // put depths in concentric circles if true, put depths top down if false
        spacingFactor: 1.75, // positive spacing factor, larger => more space between nodes (N.B. n/a if causes overlap)
        boundingBox: undefined, // constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
        avoidOverlap: true, // prevents node overlap, may overflow boundingBox if not enough space
        roots: undefined, // the roots of the trees
        maximalAdjustments: 0, // how many times to try to position the nodes in a maximal way (i.e. no backtracking)
        animate: false, // whether to transition the node positions
        animationDuration: 500, // duration of animation in ms if enabled
        animationEasing: undefined, // easing of animation if enabled
        ready: undefined, // callback on layoutready
        stop: undefined // callback on layoutstop
    };
    var cose = {
        name: 'cose',
        // Called on `layoutready`
        ready: function () {
        },
        // Called on `layoutstop`
        stop: function () {
        },
        // Whether to animate while running the layout
        animate: true,
        // The layout animates only after this many milliseconds
        // (prevents flashing on fast runs)
        animationThreshold: 250,
        // Number of iterations between consecutive screen positions update
        // (0 -> only updated on the end)
        refresh: 20,
        // Whether to fit the network view after when done
        fit: true,
        // Padding on fit
        padding: 30,
        // Constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
        boundingBox: undefined,
        // Randomize the initial positions of the nodes (true) or use existing positions (false)
        randomize: false,
        // Extra spacing between components in non-compound graphs
        componentSpacing: 100,
        // Node repulsion (non overlapping) multiplier
        nodeRepulsion: function (node) {
            return 400000;
        },
        // Node repulsion (overlapping) multiplier
        nodeOverlap: 10,
        // Ideal edge (non nested) length
        idealEdgeLength: function (edge) {
            return 10;
        },
        // Divisor to compute edge forces
        edgeElasticity: function (edge) {
            return 100;
        },
        // Nesting factor (multiplier) to compute ideal edge length for nested edges
        nestingFactor: 5,
        // Gravity force (constant)
        gravity: 80,
        // Maximum number of iterations to perform
        numIter: 1000,
        // Initial temperature (maximum node displacement)
        initialTemp: 200,
        // Cooling factor (how the temperature is reduced between consecutive iterations
        coolingFactor: 0.95,
        // Lower temperature threshold (below this point the layout will end)
        minTemp: 1.0,
        // Pass a reference to weaver to use threads for calculations
        weaver: false
    };
    var options = {
        "concentric": concentric,
        "spread": spread,
        "grid": grid,
        "circle": circle,
        "breadthfirst": breadthfirst,
        "cose": cose
    };
    var layout = nodes.layout(options[option]);
    try {
        layout.run();
    } catch (err) {
    }
}

$(document).ready(function () {
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }

            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });
    updateCy();
});
