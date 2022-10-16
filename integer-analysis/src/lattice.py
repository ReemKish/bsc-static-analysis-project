from abc import ABC, abstractmethod
from enum import Enum
from functools import reduce
import analysis

class MemberType(Enum):
    """The type of a lattice member.

    Each lattice member can either be the top element, the bottom element or some mid-level member.
    """
    TOP = 1
    VAL = 0
    BOT = -1

    def __str__(self) -> str:
        if self == MemberType.TOP: return '⊤'
        if self == MemberType.BOT: return '⊥'
        else: return 'V'

    def __repr__(self) -> str:
        return str(self)

class Lattice(ABC):
    """Represents a lattice object with a join method."""

    @abstractmethod
    def join_nontrivial(self, x, y):
        """Join two lattice members that are neither the bottom/top elements."""

    def join_trivial(self, x, y):
        """Join two lattice members in the trivial case.

        If either x or y are the bottom/top element, returns their correct
        join result, else returns None.
        """
        if self.is_bot(x): return y
        if self.is_bot(y): return x
        if self.is_top(x) or self.is_top(y): return self.top()
        return None

    def join(self, l):
        """Join a non-empty sequence of lattice members."""
        l = list(l)
        assert len(l) > 0, 'Attempted join on zero members.'
        def _join(x, y):
            z = self.join_trivial(x, y)
            return self.join_nontrivial(x, y) if z is None else z
        return reduce(_join, l)


    def top(self):
        """Returns the top element."""
        return MemberType.TOP

    def bot(self):
        """Returns the bottom element."""
        return MemberType.BOT

    def is_top(self, x) -> bool:
        """Returns True iff x is the top element."""
        return isinstance(x, type(self.top())) and x == self.top()

    def is_bot(self, x) -> bool:
        """Returns True iff x is the bottom element."""
        return isinstance(x, type(self.bot())) and x == self.bot()


    def equiv_nontrivial(self, x, y):
        """Check lattice member equality in the nontrivial case.

        Returns True iff x and y represent the same lattice member - under
        the assumption that neither x nor y are the bottom/top elements.
        """
        #  Override if equality checking is more involved than simply x == y.
        return x == y

    def equiv_trivial(self, x, y):
        """
        Checks member equality in the trivial case:
          * If either x or y are the top/bottom element,
            returns True iff x and y are the same element. 
          * If both x and y are mid-level lattice members, returns None
        """
        if (self.is_top(x) and self.is_top(y)) or \
           (self.is_bot(x) and self.is_bot(y)) :
            return True
        if self.is_top(x) != self.is_top(y) or \
           self.is_bot(x) != self.is_bot(y):
            return False
        return None

    def equiv(self, x, y):
        """
        Returns True if x and y represent the same lattice member, else False.
        """
        b = self.equiv_trivial(x, y)
        return self.equiv_nontrivial(x, y) if b is None else b


class CartProd(Lattice):
    """The Cartesian product of a sequence of lattices."""

    def __init__(self, lats):
        self.lats = lats

    def top(self):
        return tuple(lat.top() for lat in self.lats)

    def bot(self):
        return tuple(lat.bot() for lat in self.lats)

    def equiv(self, X, Y):
        return all(lat.equiv(x,y) for lat, x, y in zip(self.lats, X, Y))

    def join_nontrivial(self, X, Y):
        res = []
        for lat, x, y in zip(self.lats, X, Y):
            res.append(lat.join([x, y]))
        return tuple(res)


class DisjComp(Lattice):
    """The Disjunctive completion of a lattice."""
    def __init__(self, lat):
        self.lat = lat

    def top(self):
        return { self.lat.top() }

    def bot(self):
        return { self.lat.bot() }

    def equiv(self, X, Y):
        # Test equality by double inclusion
        return self._is_subset(X, Y) and self._is_subset(Y, X)

    def join_nontrivial(self, X, Y):
        return X.union({y for y in Y if not self._in(y, X)})

    def meet_nontrivial(self, X, Y):
        return {x for x in X if self._in(x, Y)}.union(
               {y for y in Y if self._in(y, X)})

    def _in(self, x, Y):
        """Returns True if lattice member x is in the set Y."""
        for y in Y:
            if self.lat.equiv(x, y):
                return True
        return False

    def _is_subset(self, X, Y):
        """Returns True iff X is a subset of Y.

        Both X and Y are assumed to consist soley of lattice members.
        """
        for x in X:
            if not self._in(x, Y):
                return False
        return True


class RelProd(Lattice):
    """The Relational product of a sequence of lattices."""
    # TODO
    def __init__(self, lats):
        pass

class LatticeBasedAnalysis(analysis.BaseAnalysis):
    @abstractmethod
    def lattice(self):
        """Returns the lattice on which the analysis is based."""

    def top(self):
        return self.lattice().top()

    def bottom(self):
        return self.lattice().bot()

    def join(self, l):
        return self.lattice().join(l)

    def equiv(self, x, y):
        return self.lattice().equiv(x,y)

