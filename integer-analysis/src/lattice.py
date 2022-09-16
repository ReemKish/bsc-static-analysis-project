from dataclasses import dataclass
from abc import *
from typing import Type, Tuple
from enum import Enum

class LatticeMemberTypeEnum(Enum):
    TOP = 1
    VAL = 0
    BOT = -1

@dataclass
class LatticeMemberDataType(ABC):
    @abstractmethod
    def __eq__(self, other) -> bool: pass

    @abstractmethod
    def __add__(self, other): pass

    @abstractmethod
    def __sub__(self, other): pass

    @abstractmethod
    def __str__(self) -> str: pass


@dataclass
class LatticeMember(ABC):
    val: LatticeMemberDataType
    _type: LatticeMemberTypeEnum = LatticeMemberTypeEnum.VAL

    def top(self): return self.__class__(None, _type=LatticeMemberTypeEnum.TOP)
    def bot(self): return self.__class__(None, _type=LatticeMemberTypeEnum.BOT)
    def is_top(self) -> bool: return self._type == LatticeMemberTypeEnum.TOP
    def is_bot(self) -> bool: return self._type == LatticeMemberTypeEnum.BOT

    def __eq__(self, other) -> bool:
        if isinstance(other, LatticeMember):
            return (self._type == other._type) and (self.val == other.val)
        return self.val == other

    def __add__(self, other):
        if isinstance(other, LatticeMember):
            assert self._type == other._type == LatticeMemberTypeEnum.VAL
            return LatticeMember(self.val + other.val)
        return LatticeMember(self.val + other)

    def __sub__(self, other):
        if isinstance(other, LatticeMember):
            assert self._type == other._type == LatticeMemberTypeEnum.VAL
            return LatticeMember(self.val - other.val)
        return LatticeMember(self.val - other)

    def __str__(self) -> str:
        if self.is_top(): return '⊤'
        if self.is_bot(): return '⊥'
        return str(self.val)

    @abstractmethod
    def join(self, other): pass


@dataclass
class Lattice(ABC):
    LatticeMemberType: Type[LatticeMember]

    def join(self, x: LatticeMember, y: LatticeMember) -> LatticeMember:
        return x.join(y)

    def top(self):
        return self.LatticeMemberType(None).top()

    def bot(self):
        return self.LatticeMemberType(None).bot()

    def equiv(self, x: LatticeMember, y: LatticeMember):
        return x == y

