from abc import ABC, abstractmethod
from enum import Enum
from functools import reduce


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
        return isinstance(x, MemberType) and x is MemberType.TOP

    def is_bot(self, x) -> bool:
        """Returns True iff x is the bottom element."""
        return isinstance(x, MemberType) and x is MemberType.BOT


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
        if self.is_top(x) == self.is_top(y) == True or \
           self.is_bot(x) == self.is_bot(y) == True:
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
    # TODO
    def __init__(self, lat):
        pass


class RelProd(Lattice):
    """The Relational product of a sequence of lattices."""
    # TODO
    def __init__(self, lats):
        pass

