"""Tensor class."""
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
* April: renamed tsv to tab_separated, shortened to_file
* April: renamed getSparseDict to get_sparse_dict
* May: reworked tab_separated to handle running out of memory
* comment and variable naming cleanup
"""
import math
import sys


class Tensor:
    """
    A sparse, dictionary-like implementation of square (cube, hyper-cube, etc.) 
    tensors, including basic operations allowing for linear combinations 
    (implemented in parallel).
    """

    def __init__(self, rank):
        # index field length or dimension of tensor
        self.rank = rank

        # used to map index tuples to values
        self.base_dict = {}

        # auxiliary faster cross-dimensional indices (master)
        self.midx = {}

        # index mapping unique row IDs to particular base_dict keys
        self.ridx = {}

    def __getitem__(self, key):
        # returns the value indexed by the key
        tpl = tuple(key)
        if len(tpl) == self.rank:
            if tpl in self.base_dict:
                return self.base_dict[tpl]
            else:
                return 0.0  # not present <-> zero value
        else:
            raise ValueError('Key is rank-incompatible ... key: %s, rank: %s',
                             (str(tpl), str(self.rank)))

    def __delitem__(self, key):
        # deletes the value indexed by the key (and destroys any indices)
        tpl = tuple(key)
        if tpl in self:
            del self.base_dict[tpl]
            self.midx, self.ridx = {}, {}

    def __setitem__(self, key, value):
        # sets a new value to the key index
        tpl = tuple(key)
        if len(tpl) == self.rank:
            if value != 0:
                self.base_dict[tpl] = value
            elif tpl in self.base_dict:
                # deleting if setting a value to zero
                del self.base_dict[tpl]
            self.midx, self.ridx = {}, {}
        else:
            raise ValueError('Key is rank-incompatible ... key: %s, rank: %s',
                             (str(tpl), str(self.rank)))

    def __iter__(self):
        # iterates through the list of all indices
        for key in self.base_dict:
            yield key

    def __contains__(self, key):
        # checks for the presence of key among the basic indices
        tpl = tuple(key)
        return tpl in self.base_dict

    def __len__(self):
        # returns length of the tensor in terms of non-zero indices
        return len(self.base_dict)

    def density(self):
        # density of the tensor in terms of the ratio of number of non-zero 
        # elements w.r.t. the maximum possible number of elements in the current
        # tensor
        unique_indvals = set()
        for key in self.base_dict:
            unique_indvals |= set(key)
            return float(len(self.base_dict)) / (len(unique_indvals) ** self.rank)

    def dim_size(self, dim):
        # size of a dimension (i.e., number of unique index IDs in a dimension)
        # WARNING: can be relatively slow for large/dense tensors
        if dim >= self.rank:
            return 0
        return len(set([x[dim] for x in self.base_dict]))

    def lex_size(self):
        # return the current lexicon size
        unique_indvals = set()
        for key in self.base_dict:
            unique_indvals |= set(key)
            return len(unique_indvals)

    def items(self):
        # return all the (key,value) tuples of the tensor
        return self.base_dict.items()

    def keys(self):
        # return all the keys of the tensor
        return self.base_dict.keys()

    def values(self):
        # return all the values of the tensor
        return self.base_dict.values()

    def has_key(self, key):
        # checks for the presence of the key among the tensor indices
        return key in self.base_dict

    def __eq__(self, other):
        if not isinstance(other, Tensor):
            raise NotImplementedError('Cannot compare tensor with a non-tensor: %s',
                                      (str(type(other)),))
        if self.rank != other.rank:
            return False
        return self.base_dict == other.base_dict

    def __ne__(self, other):
        return not self.__eq__(other)

    def __add__(self, other):
        # tensor addition operator
        try:
            if self.rank != other.rank:
                raise NotImplementedError('Cannot add two tensors of different ranks')
        except AttributeError:
            raise NotImplementedError('Cannot add %s to tensor', (str(type(other)),))
        result = Tensor(rank=self.rank)
        # sequential processing
        for key in set(other.keys() + self.keys()):
            value = self.__getitem__(key) + other[key]
            if value:
                # if the addition is not zero, set it to the resulting tensor
                result[key] = value
        return result

    def __mul__(self, other):
        # scalar*tensor multiplication (aT, where a, T are the scalar and tensor
        # expressions, respectively)
        if type(other) not in [int, float]:
            raise NotImplementedError('Wrong scalar type: %', (str(type(other)),))
        if other == 0:
            return Tensor(rank=self.rank)
        result = Tensor(rank=self.rank)
        # sequential processing
        for key in self.base_dict:
            result[key] = other * self.base_dict[key]
        return result

    def __rmul__(self, other):
        # scalar*tensor multiplication (swapped operators to allow Ta being
        # computed as aT)
        return self * other

    def __or__(self, other):
        # max-based element-wise aggregation of two tensors
        try:
            if self.rank != other.rank:
                raise NotImplementedError('Cannot aggregate tensors of different' +
                                          ' ranks')
        except AttributeError:
            raise NotImplementedError('Cannot aggregate %s with a tensor',
                                      (str(type(other)),))
        result = Tensor(rank=self.rank)
        # sequential processing
        for key in set(other.keys() + self.keys()):
            value = max(self.__getitem__(key), other[key])
            if value:
                # if the result is not zero, set it to the output tensor
                result[key] = value
        return result

    def __and__(self, other):
        # min-based element-wise aggregation of two tensors
        try:
            if self.rank != other.rank:
                raise NotImplementedError('Cannot aggregate tensors of different' +
                                          ' ranks')
        except AttributeError:
            raise NotImplementedError('Cannot aggregate %s with a tensor',
                                      (str(type(other)),))
        result = Tensor(rank=self.rank)
        # sequential processing
        for key in set(other.keys() + self.keys()):
            value = min(self.__getitem__(key), other[key])
            if value:
                # if the result is not zero, set it to the output tensor
                result[key] = value
        return result

    def __iadd__(self, other):
        return self.__add__(other)

    def __imul__(self, other):
        return self.__mul__(other)

    def __iand__(self, other):
        return self.__and__(other)

    def __ior__(self, other):
        return self.__or__(other)

    def normalise(self):
        # abs-sum normalisation of the tensor values
        result = Tensor(rank=self.rank)
        n = float(sum([math.fabs(x) for x in self.base_dict.values()]))
        for key in self.base_dict:
            result[key] = self.base_dict[key] / n
        return result

    def index(self):
        """
        @TODO - write up the documentation
        """

        # @TODO - do a bit of compl. analysis and profiling here - why so slow?

        # resetting the indices
        self.ridx, self.midx = {}, {}
        # contructing the row ID -> key index and dimension ID -> key element ->
        # set of row IDs indices in one pass through the base dictionary
        for rid, key in [(x, self.base_dict.keys()[x]) for x in range(len(self.base_dict))]:
            # updating the row ID index
            self.ridx[rid] = key
            # adding the row ID to the key element value sets
            for (key_dim, key_elem) in [(x, key[x]) for x in range(len(key))]:
                if key_dim not in self.midx:
                    self.midx[key_dim] = {}
                if key_elem not in self.midx[key_dim]:
                    self.midx[key_dim][key_elem] = []
                self.midx[key_dim][key_elem].append(rid)
        # changing the filled end lists in the index to sets
        for key_dim in self.midx:
            for key_elem in self.midx[key_dim]:
                self.midx[key_dim][key_elem] = set(self.midx[key_dim][key_elem])

    def query_and(self, query):
        """
        @TODO - write up the documentation
        """

        if self.midx == {} and self.ridx == {}:
            raise AttributeError('Tensor index not computed, use index() first')
        # initialise the matching row IDs set
        row_ids = set(self.ridx.keys())
        # proceed through the query, intersecting the row IDs according to it
        for query_dim, query_elem in [(x, query[x]) for x in range(len(query))]:
            if query_dim not in self.midx:
                continue  # weird, shouldn't happen, but have it here for sure
            if query_elem is not None:
                if query_elem in self.midx[query_dim]:
                    row_ids &= self.midx[query_dim][query_elem]
            else:
                # if an index element is not present, result is empty
                row_ids = set()
                break
        # generating the (key,value) tuples from the matching row IDs
        return [(self.ridx[x], self.base_dict[self.ridx[x]]) for x in row_ids]

    def query_or(self, query):
        """
        @TODO - write up the documentation
        """

        if self.midx == {} and self.ridx == {}:
            raise AttributeError('Tensor index not computed, use index() first')
        # initialise the matching row IDs set
        # @TODO - think about the correctness of the semantics in case of 
        #         all-None queries!
        row_ids = set()
        # proceed through the query, unioning the row IDs according to it
        for query_dim, query_elem in [(x, query[x]) for x in range(len(query))]:
            if query_dim not in self.midx:
                continue  # weird, shouldn't happen, but have it here for sure
            if query_elem is not None and query_elem in self.midx[query_dim]:
                row_ids |= self.midx[query_dim][query_elem]
        # generating the (key,value) tuples from the matching row IDs
        return [(self.ridx[x], self.base_dict[self.ridx[x]]) for x in row_ids]

    def query(self, query, qtype='AND'):
        """
        @TODO - write up the documentation
        """
        if qtype.lower() == 'and':
            return self.query_and(query)
        elif qtype.lower() == 'or':
            return self.query_or(query)
        else:
            raise NotImplementedError('Unknown query type %s, try AND or OR',
                                      (qtype,))

    def matricise(self, pivot_dim):
        """
        Creates a matrix representation of the tensor, using the given dimension
        as a pivot. The result is a tensor of rank 2 with keys in the form 
        (dim_p,(dim_0,...,dim_(p-1),dim_(p+1),...,dim_rank)) and values 
        representing the corresponding original tensor values.
        """

        matrix = Tensor(rank=2)
        try:
            # iterable (multiple) pivot dimensions
            if max(pivot_dim) >= self.rank:
                raise NotImplementedError('Max. dimension of %s higher than rank %s',
                                          (str(pivot_dim), str(self.rank)))
            for key, value in self.base_dict.items():
                col_ids, row_ids = [], []
                for i, key_elem in [(x, key[x]) for x in range(len(key))]:
                    if i in pivot_dim:
                        row_ids.append(key_elem)
                    else:
                        col_ids.append(key_elem)
                row_ids = tuple(row_ids)
                col_ids = tuple(col_ids)
                if len(col_ids) == 1:
                    col_ids = col_ids[0]
                if len(row_ids) == 1:
                    row_ids = row_ids[0]
                matrix[(row_ids, col_ids)] = value
        except TypeError as e:
            print(e)
            # single pivot dimension
            # the only one currently implemented
            if pivot_dim >= self.rank:
                raise NotImplementedError('Dimension %s higher than rank %s',
                                          (str(pivot_dim), str(self.rank)))
            for key, value in self.base_dict.items():
                # keys are tuples in the format (X close to Y)
                # value is the calculated weight from knowledge_base_create()
                column_id = tuple(key[:pivot_dim] + key[pivot_dim + 1:])
                matrix[(key[pivot_dim], column_id)] = value
        return matrix

    def get_sparse_dict(self, col2row=True):
        # returns a sparse matrix in a simple dictionary representation that can be
        # directly used for retrieving whole rows (applicable only to matrices); 
        # optionally also an index mapping column IDs to set of rows that have a 
        # non-zero element in that column
        if self.rank != 2:
            raise NotImplemented('Not applicable for tensors of rank %s',
                                 (self.rank,))
        dct, idx = {}, {}
        for (i, j), w in self.items():
            if i not in dct:
                dct[i] = {}
            dct[i][j] = w
            # updating the column 2 row index
            if col2row:
                if j not in idx:
                    idx[j] = set()
                idx[j].add(i)
        if col2row:
            return dct, idx
        return dct

    def __str__(self):
        """
        Generates a string representation of the tensor in the form of a table
        mapping the keys to values.
        """

        return '\n'.join(['\t'.join([str(elem) for elem in key]) + ' -> ' +
                          str(self.base_dict[key]) for key in self.base_dict])

    def tab_separated(self, split_into=3, last_done=0):
        """
        Generates a string with tab-separated values representing the tensor.
        """

        try:
            tsv = '\n'.join(['\t'.join([str(elem) for elem in key] +
                                       [str(self.base_dict[key])]) for key in self.base_dict])
        except MemoryError:
            upper_limit = (last_done + 1) * len(self.base_dict) / split_into
            lower_limit = last_done * len(self.base_dict) / split_into
            tsv = dict(self.base_dict.items()[lower_limit:upper_limit])
            last_done += 1
        return tsv, last_done

    def to_file(self, filename):
        """
        Exporting a lexicon to a filename or file-like object (tab-separated 
        values).
        """

        content, last_done = self.tab_separated()
        # print(f"OLD SYSTEM, {filename} SIZE: {len(content)}")
        filename.write(content.encode())
        filename.flush()
        while 0 < last_done < 3:
            content, last_done = self.tab_separated(last_done=last_done)
            filename.write(content.encode())
            filename.flush()

    def from_file(self, filename):
        """
        Importing a tensor from a filename or a file-like object (tab-separated
        values).
        """
        try:
            # assuming a file object
            lines = filename.read().decode("utf-8").split('\n')
        except AttributeError:
            # assuming a filename
            lines = open(filename, 'r').read().split('\n')
        for line in lines:
            key_val = line.split('\t')[:self.rank + 1]
            key = tuple(x for x in key_val[:-1])
            val = float(key_val[-1])
            self.base_dict[key] = val
