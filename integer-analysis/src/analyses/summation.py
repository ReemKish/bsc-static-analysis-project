class AbsVal:
    """Abstract Value.
    Represents a value that may contain an unknown ('?').
    """
    def __init__(self, unknown=None, const=0):
        self.const = const
        self.unknown = unknown

    def inc(self):
        self.const += 1

    def dec(self):
        self.const -= 1

    def __add__(self, other):
        assert isinstance(other, int)
        return AbsVal(unknown=self.unknown, const=self.const + other)

    def __sub__(self, other):
        return self.__add__(-1 * other)

    def __repr__(self):
        return f"AbsVal(unknown={self.unknown}, const={self.const})"

    def __str__(self):
        if self.unknown and self.const:
            return f"?{self.unknown}{self.const:+}"
        if self.unknown:
            return f"?{self.unknown}"
        return f"{self.const}"
