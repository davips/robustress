#  Copyright (c) 2024. Davi Pereira dos Santos
#  This file is part of the sortedness project.
#  Please respect the license - more about this in the section (*) below.
#
#  sortedness is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  sortedness is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with sortedness.  If not, see <http://www.gnu.org/licenses/>.
#
#  (*) Removing authorship by any means, e.g. by distribution of derived
#  works or verbatim, obfuscated, compiled or rewritten versions of any
#  part of this work is illegal and it is unethical regarding the effort and
#  time spent here.
#
from torch import tensor

from sortedness.new.quality._elementwise import Elementwise
from sortedness.new.quality.measure.elementwise import calmness


class Calmness(Elementwise):
    def __init__(self, X: tensor, w: tensor = None, sortbyX_=True):
        """Calmness according to transformed data when `sortbyX_=True`

        >>> from torch import tensor
        >>> X = tensor([[1.,2], [3,4], [5,6], [7,8]])
        >>> w = tensor([0.5, 0.3, 0.25])
        >>> Calmness(X, w)(X)
        tensor(1.)
        >>> X_ = tensor([[3.,4], [1,2], [5,6], [7,8]])
        >>> Calmness(X, w)(X_)
        tensor(0.7825)

        :param X: Original data.
        :param w: Weights vector. |w| < |X|. Only the first |w| neighbors are used - for efficiency.
        :param sortbyX_: If `True`, sort according to transformed data (X_, instead of X).
        :return:
        """
        super().__init__(calmness, X, w, sortbyX_)
