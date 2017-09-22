# Tools for Concurrent Kleene Algebra

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.926651.svg)](https://doi.org/10.5281/zenodo.926651)

_Requires Python 3.4 or newer._

This repository contains a small Python library that supports manipulation of (and, to a limited degree, reasoning about) terms in _Concurrent Kleene Algebra_, a formalism that can be used to model concurrent program flow.

Besides utility functions for building terms Python-style, this library has functionality that calculates the _syntactic closure_ of a _Weak_ CKA term (without parallel star), which is an equivalent WCKA term whose _Weak Bi-Kleene Algebra_ semantics coincide with the WCKA semantics.
This syntactic closure can, for instance, be used to leverage an existing WBKA equivalence checking algorithm in order to decide the equational theory of WCKA.

## Usage
First, import the library
```python
>>> import wcka
```
To compose terms, use `+` for non-deterministic composition, `**` for sequential composition, `//` for parallel composition and `.star()` for the Kleene star.
Primitive symbols can be created using the `Primitive` class.
For instance:
```python
>>> a = wcka.Primitive('a')
>>> b = wcka.Primitive('b')
>>> c = wcka.Primitive('c')
>>> d = wcka.Primitive('d')
>>> (a + b.star) // (c ** d)
<Parallel '(a + b*)‖cd'>
```
Note that the native operator precedence of Python matches the canonical precedence for WCKA terms: `.star()` comes before `**`, followed by `//`, which precedes `+`.

To calculate the preclosure of a parallel composition, call `.preclosure()`:
```python
>>> (a // b // c).preclosure()
<Choice '(a‖c + a‖c + c‖a)‖b + b‖(a‖c + a‖c + c‖a) + (a‖b + a‖b + b‖a)‖c + a‖(b‖c + c‖b + b‖c) + (b‖c + c‖b + b‖c)‖a + c‖(a‖b + a‖b + b‖a)'>
```

To calculate the closure of any term, call `.closure()`:
```python
>>> (a // b).closure()
<Choice 'a‖b + a‖b + b‖a + ba + ab'>
```

You can also inspect the linear system generated for computing the closure of a parallel term:
```python
>>> str((a // b).linear_system())
1 + X[1‖1] ≤ X[1‖1]
a + aX[1‖1] + X[a‖1] ≤ X[a‖1]
b + bX[1‖1] + X[1‖b] ≤ X[1‖b]
a‖b + (a‖b + b‖a + a‖b)X[1‖1] + bX[a‖1] + aX[1‖b] + X[a‖b] ≤ X[a‖b]
```

Note that results are not deterministic, due to the fact that sets do not have a canonical order in Python, and the underlying algorithm iterates over sets in a number of places.
