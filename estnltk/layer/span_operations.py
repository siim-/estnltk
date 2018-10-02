from typing import Union
from estnltk import Span, EnvelopingSpan, AmbiguousSpan


#  Layer operations are ported from:
#    https://github.com/estnltk/estnltk/blob/master/estnltk/single_layer_operations/layer_positions.py


def touching_right(x: Span, y: Span) -> bool:
    """
    Tests if Span y is touching this Span (x) from the right.
    Pictorial example:
    xxxxxxxx
            yyyyy
    """
    assert isinstance(x, Span), x
    assert isinstance(y, Span), y
    return x.end == y.start


def touching_left(x: Span, y: Span) -> bool:
    """
    Tests if Span y is touching this Span (x) from the left.
    Pictorial example:
         xxxxxxxx
    yyyyy
    """
    assert isinstance(x, Span), x
    assert isinstance(y, Span), y
    return touching_right(y, x)


def hovering_right(x: Span, y: Span) -> bool:
    """
    Tests if Span y is hovering right from x.
    Pictorial example:
    xxxxxxxx
              yyyyy
    """
    assert isinstance(x, Span), x
    assert isinstance(y, Span), y
    return x.end < y.start


def hovering_left(x: Span, y: Span) -> bool:
    """
    Tests if Span y is hovering left from x.
    Pictorial example:
            xxxxxxxx
    yyyyy
    """
    assert isinstance(x, Span), x
    assert isinstance(y, Span), y
    return hovering_right(y, x)


def right(x: Span, y: Span) -> bool:
    """
    Tests if Span y is either touching or hovering right with respect to this Span.
    """
    assert isinstance(x, Span), x
    assert isinstance(y, Span), y
    return touching_right(x, y) or hovering_right(x, y)


def left(x: Span, y: Span) -> bool:
    """
    Tests if Span y is either touching or hovering left with respect to this Span.
    """
    assert isinstance(x, Span), x
    assert isinstance(y, Span), y
    return right(y, x)


def nested(x: Span, y: Span) -> bool:
    """
    Tests if Span y is nested inside x.
    Pictorial example:
    xxxxxxxx
      yyyyy
    """
    assert isinstance(x, Span), x
    assert isinstance(y, Span), y
    return x.start <= y.start <= y.end <= x.end


def equal(x: Span, y: Span) -> bool:
    """
    Tests if Span y is positionally equal to x.
    (Both are nested within each other).
    Pictorial example:
    xxxxxxxx
    yyyyyyyy
    """
    assert isinstance(x, Span), x
    assert isinstance(y, Span), y
    return nested(x, y) and nested(y, x)


span = Union[Span, EnvelopingSpan, AmbiguousSpan]


def equal_support(x: span, y: span) -> bool:
    if isinstance(x, AmbiguousSpan):
        x = x.span
        return equal_support(x, y)
    if isinstance(y, AmbiguousSpan):
        y = y.span
        return equal_support(x, y)
    if isinstance(x, EnvelopingSpan):
        return isinstance(y, EnvelopingSpan) and x.spans == y.spans
    if isinstance(x, Span):
        return isinstance(y, Span) and x.start == y.start and x.end == y.end
    raise TypeError('unexpected type of x: ' + str(type(x)))


def symm_diff_ambiguous_spans(x: AmbiguousSpan, y: AmbiguousSpan):
    assert isinstance(x, AmbiguousSpan)
    assert isinstance(y, AmbiguousSpan)
    annot_x = [a for a in x if a not in y]
    annot_y = [a for a in y if a not in x]
    return annot_x, annot_y


def nested_aligned_right(x: Span, y: Span) -> bool:
    """
    Tests if Span y is nested inside x, and
    Span y is aligned with the right ending of this Span.
    Pictorial example:
    xxxxxxxx
       yyyyy
    """
    assert isinstance(x, Span), x
    assert isinstance(y, Span), y
    return nested(x, y) and x.end == y.end


def nested_aligned_left(x: Span, y: Span) -> bool:
    """
    Tests if Span y is nested inside x, and
    Span y is aligned with the left ending of this Span.
    Pictorial example:
    xxxxxxxx
    yyyyy
    """
    assert isinstance(x, Span), x
    assert isinstance(y, Span), y
    return nested(x, y) and x.start == y.start


def overlapping_left(x: Span, y: Span) -> bool:
    """
    Tests if left side of x overlaps with
    the Span y, but y is not nested within this Span.
    Pictorial example:
      xxxxxxxx
    yyyyy
    """
    assert isinstance(x, Span), x
    assert isinstance(y, Span), y
    return y.start < x.start < y.end


def overlapping_right(x: Span, y: Span) -> bool:
    """
    Tests if right side of x overlaps with
    the Span y, but y is not nested within this Span.
    Pictorial example:
    xxxxxxxx
          yyyyy
    """
    assert isinstance(x, Span), x
    assert isinstance(y, Span), y
    return y.start < x.end < y.end


def conflict(x: Span, y: Span) -> bool:
    """
    Tests if there is a conflict between the Span x and the
    Span y: one of the Spans is either nested within other,
    or there is an overlapping from right or left side.
    """
    assert isinstance(x, Span), x
    assert isinstance(y, Span), y
    return nested(x, y) or nested(y, x) or \
           overlapping_left(x, y) or overlapping_right(x, y)