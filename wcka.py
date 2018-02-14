from abc import ABC, abstractmethod

class Term(ABC):
    """
    Represents a term of CKA. Includes operator overloads for composing terms,
    as well as comparison operators.
    """

    def __add__(self, other):
        """
        Returns the sum of the two input terms, normalized for units.
        """

        if type(other) is Zero:
            return self
        elif type(self) is Zero:
            return other
        elif other in self:
            return self
        elif self in other:
            return other
        else:
            return Choice(self, other)

    def __pow__(self, other):
        """
        Returns the sequential composition of the two input terms, normalized
        for annihilation and units.
        """

        if type(other) is One:
            return self
        elif type(self) is One:
            return other
        elif type(other) is Zero:
            return Zero()
        elif type(self) is Zero:
            return Zero()
        else:
            return Sequential(self, other)

    def __floordiv__(self, other):
        """
        Returns the parallel composition of the two input terms, normalized
        for annihilation and units.
        """

        if type(other) is One:
            return self
        elif type(self) is One:
            return other
        elif type(other) is Zero:
            return Zero()
        elif type(self) is Zero:
            return Zero()
        else:
            return Parallel(self, other)

    def star(self):
        """
        Returns the starred version of the current term.
        """

        if type(self) is One or type(self) is Zero:
            return One()
        else:
            return Star(self)

    def remainders(self, seen=set()):
        """
        Calculates the set of sequential remainders of a term.
        """

        todo = self.ssplicings()
        remainders = {self} | seen

        while todo:
            _, expand = todo.pop()
            if expand not in remainders:
                remainders |= expand.remainders(remainders)

        return remainders

    def bracket(self, next_op):
        """
        Returns term or its bracketed version based on the operator next_op
        that this term will be wrapped in.
        """

        def precedes(a, b):
            """
            Convenience function for determining whether one operator precedes
            another operator.
            """
            order = [
                Zero,
                One,
                Primitive,
                Variable,
                Star,
                Sequential,
                Parallel,
                Choice
            ]

            try:
                return order.index(a) <= order.index(b)
            except ValueError:
                return False

        if precedes(self.__class__, next_op.__class__):
            return "%s" % self
        else:
            return "(%s)" % self

    def __repr__(self):
        return "<%s '%s'>" % (self.__class__.__name__, str(self))

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def __contains__(self, term):
        return self == term


class ClosedTerm(Term):
    """
    Represents a term without variables.
    """

    def psplicings(self):
        """
        Returns the parallel splicings of this term as a set of pairs.
        """

        return self.nontrivial_psplicings() | { (self, One()), (One(), self) }

    @abstractmethod
    def nontrivial_psplicings(self):
        """
        Returns the parallel splicings of this term as a set of pairs,
        excluding the two trivial splicings that have the term itself on one
        side, and a "1" term on the other side.
        """

    @abstractmethod
    def ssplicings(self):
        """
        Returns the sequential splicings of this term as a set of pairs.
        """

    @abstractmethod
    def closure(self):
        """
        Calculates the closure of this term.
        """

    @abstractmethod
    def nullable(self):
        """
        Returns a boolean indicating whether this term is nullable.
        """

    def width(self):
        """
        Returns the width of this term.
        """

        return 0 if self.is_trivial() else self.nontrivial_width()

    @abstractmethod
    def is_trivial(self):
        """
        Returns whether this term is trivial (i.e., has empty semantics).
        """

    @abstractmethod
    def nontrivial_width(self):
        """
        Returns the width of this term, assuming it is not trivial.
        """

    @abstractmethod
    def __str__(self):
        """
        Returns this term represented as a human-readable string.
        """


class Zero(ClosedTerm):
    """
    Represents a zero term.
    """

    def nontrivial_psplicings(self):
        return set()

    def ssplicings(self):
        return set()

    def closure(self):
        return self

    def nullable(self):
        return False

    def is_trivial():
        return True

    def nontrivial_width(self):
        return 0

    def __str__(self):
        return "0"


class One(ClosedTerm):
    """
    Represents a one term.
    """

    def __add__(self, other):
        if type(other) is Sequential:
            if type(other.left) is Star and other.left.beneath == other.right:
                return other.left   # 1 + a*a
            elif (type(other.right) is Star and
                  other.right.beneath == other.left):
                return other.right  # 1 + aa*

        return super().__add__(other)

    def nontrivial_psplicings(self):
        return set()

    def ssplicings(self):
        return { (self, self) }

    def closure(self):
        return self

    def nullable(self):
        return True

    def is_trivial(self):
        return False

    def nontrivial_width(self):
        return 0

    def __str__(self):
        return "1"


class Primitive(ClosedTerm):
    """
    Represents a primitive term.
    """

    def __init__(self, letter):
        self.letter = letter

    def nontrivial_psplicings(self):
        return set()

    def ssplicings(self):
        return { (self, One()), (One(), self) }

    def closure(self):
        return self

    def nullable(self):
        return False

    def is_trivial(self):
        return False

    def nontrivial_width(self):
        return 1

    def __str__(self):
        return self.letter


class BinaryTerm(ClosedTerm):
    """
    Base class for a term with a binary operator at the top.
    """

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __str__(self):
        return "%s%s%s" % (
            self.left.bracket(self),
            self.operator,
            self.right.bracket(self)
        )


class Choice(BinaryTerm):
    """
    Represents the sum of two terms as a term.
    """

    operator = " + "

    def nontrivial_psplicings(self):
        return self.left.psplicings() | self.right.psplicings()

    def ssplicings(self):
        return self.left.ssplicings() | self.right.ssplicings()

    def closure(self):
        return self.left.closure() + self.right.closure()

    def is_trivial(self):
        return self.left.is_trivial() and self.right.is_trivial()

    def nontrivial_width(self):
        return max(self.left.width(), self.right.width())

    def nullable(self):
        return self.left.nullable() or self.right.nullable()

    def __contains__(self, term):
        return self == term or term in self.left or term in self.right


class Sequential(BinaryTerm):
    """
    Represents the sequential composition of two terms as a term.
    """

    operator = ""

    def __add__(self, other):
        if type(other) is One:
            if type(self.left) is Star and self.left.beneath == self.right:
                return self.left   # a*a + 1
            elif type(self.right) is Star and self.right.beneath == self.left:
                return self.right  # aa* + 1

        return super().__add__(other)

    def nontrivial_psplicings(self):
        return {
            (g, h)
            for (g, h) in self.left.psplicings()
            if self.right.nullable()
        } | {
            (g, h)
            for (g, h) in self.right.psplicings()
            if self.left.nullable()
        }

    def ssplicings(self):
        return {
            (self.left ** g, h) for (g, h) in self.right.ssplicings()
        } | {
            (g, h ** self.right) for (g, h) in self.left.ssplicings()
        }

    def closure(self):
        return self.left.closure() ** self.right.closure()

    def nullable(self):
        return self.left.nullable() and self.right.nullable()

    def is_trivial(self):
        return self.left.is_trivial() or self.right.is_trivial()

    def nontrivial_width(self):
        return max(self.left.width(), self.right.width())


class Parallel(BinaryTerm):
    """
    Represents the parallel composition of two terms as a term.
    """

    operator = "‖"

    def nontrivial_psplicings(self):
        return {
            (g1 // g2, h1 // h2)
            for (g1, h1) in self.left.psplicings()
            for (g2, h2) in self.right.psplicings()
        }

    def ssplicings(self):
        return {
            (g1 // g2, h1 // h2)
            for (g1, h1) in self.left.ssplicings()
            for (g2, h2) in self.right.ssplicings()
        }

    def preclosure(self):
        """
        Computes the preclosure of this parallel composition.
        """

        return sum(
            (
                g.closure() // h.closure()
                for (g, h) in self.psplicings()
                if g.width() < self.width() and h.width() < self.width()
            ),
            self.left // self.right
        )

    def linear_system(self):
        symbols = {
            Parallel(lprime, rprime)
            for lprime in self.left.remainders()
            for rprime in self.right.remainders()
        }

        vector = {
            symbol: symbol.left // symbol.right  # Fold if possible
            for symbol in symbols
        }

        matrix = {
            (s1, s2): sum(
                (
                    Parallel(g1, g2).preclosure()
                    for (g1, h1) in s1.left.ssplicings()
                    for (g2, h2) in s1.right.ssplicings()
                    if Parallel(h1, h2) == s2
                ),
                Zero()
            )
            for s1 in symbols
            for s2 in symbols
        }

        return LinearSystem(symbols, matrix, vector)

    def closure(self):
        solution = self.linear_system().solve()

        return solution[self]

    def nullable(self):
        return self.left.nullable() and self.right.nullable()

    def is_trivial(self):
        return self.left.is_trivial() or self.right.is_trivial()

    def nontrivial_width(self):
        return self.left.width() + self.right.width()

    def __contains__(self, other):
        if type(other) is Parallel:
            return ((other.left in self.left and other.right in self.right) or
                    (other.left in self.right and other.right in self.left))
        else:
            return super().__contains__(other)


class Star(ClosedTerm):
    """
    Represents a term below a Kleene star.
    """

    def __init__(self, beneath):
        self.beneath = beneath

    def nontrivial_psplicings(self):
        return self.beneath.psplicings()

    def ssplicings(self):
        return {
            (self ** g, h ** self)
            for (g, h) in self.beneath.ssplicings()
        } | {
            (One(), One())
        }

    def closure(self):
        return self.beneath.closure().star()

    def nullable(self):
        return True

    def is_trivial(self):
        return False

    def nontrivial_width(self):
        return self.beneath.width()

    def star(self):
        return self

    def __str__(self):
        return "%s*" % self.beneath.bracket(self)

    def __contains__(self, other):
        if type(other) is One:
            return True
        elif other in self.beneath:
            return True
        else:
            return super().__contains__(other)

class Variable(Term):
    """
    Represents a variable.
    """

    def __init__(self, name, index):
        self.name = name
        self.index = index

    def __str__(self):
        return "%s[%s]" % (self.name, self.index)


class LinearSystem:
    """
    Represents a system of linear inequations.
    """

    def __init__(self, symbols, matrix, vector):
        self.symbols = symbols
        self.matrix = matrix
        self.vector = vector

    def variable(self, symbol):
        return Variable("X", symbol)

    def solve(self):
        elim = next(iter(self.symbols))
        reuse = self.symbols - { elim }

        if not reuse:
            # Base: use the fixpoint axiom of KA to find a solution
            solution = {
                elim: self.matrix[elim, elim].star() ** self.vector[elim]
            }
        else:
            # Induction: eliminate one variable and recurse
            subvector = {
                v: self.vector[v] + self.matrix[v, elim] ** self.vector[elim]
                for v in reuse
            }

            submatrix = {
                (v1, v2):
                self.matrix[v1, elim] **
                self.matrix[elim, elim].star() **
                self.matrix[elim, v2]
                + self.matrix[v1, v2]
                for v1 in reuse
                for v2 in reuse
            }

            subsystem = LinearSystem(reuse, submatrix, subvector)

            solution = subsystem.solve()
            solution[elim] = \
                self.matrix[elim, elim].star() ** \
                sum(
                    (self.matrix[elim, v] ** solution[v] for v in reuse),
                    self.vector[elim]
                )

        return solution

    def __str__(self):
        """
        Represents the linear system as a series of human-readable inequations.
        """
        lines = []
        for s1 in self.symbols:
            left = sum(
                (
                    self.matrix[s1, s2] ** self.variable(s2)
                    for s2 in self.symbols
                ),
                self.vector[s1]
            )

            lines.append("%s ≤ %s" % (left, self.variable(s1)))

        return "\n".join(lines)
