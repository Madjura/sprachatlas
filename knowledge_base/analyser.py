__copyright__ = """
Copyright (C) 2017 Thomas Huber <huber150@stud.uni-passau.de, madjura@gmail.com>
Copyright (C) 2012 Vit Novacek (vit.novacek@deri.org), Digital Enterprise
Research Institute (DERI), National University of Ireland Galway (NUIG)
All rights reserved.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

// Modifications made to the original code by Vit Novacek
----------------
2017, Thomas Huber
* March: reworked to use string representation for everything instead of int<->string mapping for tokens
* April: reworked to use NeoMemstore instead of Skimmr memstore
* April: removed __del__, getMostSpecificTerms functions
* April: similarTo renamed to similar_to
* May: removed code for perspectives, only one is used
* comment and variable naming cleanup
"""
import math


class Analyser:
    """
    Basic class for matrix perspective analysis, offering the following services:
      - clustering of the input matrix rows 
      - learning of rules from the perspective and its compressed counterpart
    """

    def __init__(self, trace=False, matrix=None):
        """Initialising the class with an input matrix to be analysed."""
        self.trace = trace
        # the matrix handler of the perspective, computed from scratch by default
        self.matrix = matrix
        # <token>: {(close to, <token2>): value}
        self.sparse = None
        # (close to, <token>): [<tokens>], essentially the reverse of self.sparse
        self.col2row = None
        # get an in-memory representation of the matrix
        self.sparse, self.col2row = self.matrix.get_sparse_dict()

    def similar_to(self, subject: str, top=100, minsim=0.001):
        """Calculates tokens similar to a given one."""
        if subject is None or subject not in self.sparse:
            return []
        # the row vector of the sparse matrix (a column_index:weight dictionary)
        #                 paul     ball     roof
        # close to, paul   1.0      0.8      0.3
        # close to, roof   0.6      0.5      0.2
        # close to, ball   0.3      0.3      1.0
        # values are examples
        # sparse[paul] = [(close to, paul): 1.0, (close to, roof): 0.6, (close to, ball: 0.3)]
        row = self.sparse[subject]

        # length of row
        # sum = 1.0**2 + 0.6**2 + 0.3**2 = 1.45
        # sqrt(sum) = 0.6708
        un = 0
        # TODO: check why this happens
        for expression in row:
                val = row[expression] or 0
                un += val ** 2
        un = math.sqrt(un)
        # un = math.sqrt(sum([row[expression] ** 2 for expression in row]))

        # promising holds all expressions that are possibly relevant
        # paul, roof, ball
        promising = set()
        for col in row:
            promising |= self.col2row[col]
        if self.trace:
            print("similar_to() - subject vector size        :", len(row))
            print("similar_to() - number of possibly similar:", len(promising))
        sim_vec = []
        # now check all possibly relevant expressions for actual relevancy
        # paul, roof, ball
        for possible in promising:
            # ignore same, no reason to check
            if possible == subject:
                continue
            # example: roof
            # paul: 0.3, roof: 0.2, ball: 1.0
            compared_row = self.sparse[possible]
            # computing the actual similarity
            uv = 0.0
            vn = 0.0
            # first iterate over the column values
            # then get the row values for each of the column vlues -> this is compared_row
            for expression in compared_row:
                # TODO: check why this happens
                val2 = compared_row[expression] or 0
                # then check if the column values of the compared_row appear in the original row
                if expression in row:
                    # example: paul and ball
                    # row[(close to, paul)] = 1.0
                    # compared_row[(close to, paul)] = 0.3
                    # uv += 0.3
                    # TODO: check why this happens
                    val = row[expression] or 0
                    uv += val * val2
                vn += val2 ** 2
            # vn is length of compared_row after sqrt
            vn = math.sqrt(vn)
            # vn is length of compared, un is length of original
            # uv is the product of weights of entries that are in both rows
            sim = float(uv) / (un * vn)
            if math.fabs(sim) >= minsim:
                # add only if similarity crosses the threshold (adding code 
                # translated from the sparse representation row index)
                sim_vec.append((sim, possible))
        if self.trace:
            print("similar_to() - number of actually similar:", len(sim_vec))
            print("similar_to() - sorting and converting the results now")
        # getting the (similarity, row vector ID) tuples sorted
        sorted_tuples = sorted(sim_vec, key=lambda expression: expression[0], reverse=True)
        return [(expression[1], expression[0]) for expression in sorted_tuples[:top]]
