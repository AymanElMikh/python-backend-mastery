"""
Demo: Exception Chaining — __cause__, __context__, __suppress_context__
Run:  python demo.py
"""

import sys
import traceback

# ── Section 1: Implicit chaining — raise inside except ───────────────────────
def implicit_chain():
    try:
        int("not_a_number")     # raises ValueError
    except ValueError:
        raise RuntimeError("Processing failed")  # __context__ set automatically


# ── Section 2: Explicit chaining — raise X from Y ────────────────────────────
class DatabaseError(Exception):
    """Wraps low-level DB errors at the service layer."""

def explicit_chain():
    try:
        {}["missing_key"]       # KeyError (simulating db error)
    except KeyError as e:
        raise DatabaseError("Record lookup failed") from e  # __cause__ set


# ── Section 3: Suppressing the chain — raise X from None ─────────────────────
class NotFoundError(Exception):
    pass

def suppressed_chain(key):
    internal_cache = {}
    try:
        return internal_cache[key]
    except KeyError:
        raise NotFoundError(f"No entry for {key!r}") from None  # suppress KeyError


# ── Section 4: Walking the chain programmatically ────────────────────────────
def walk_chain(exc):
    chain = []
    seen = set()
    current = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        suppress = getattr(current, '__suppress_context__', False)
        chain.append({
            "type": type(current).__name__,
            "msg": str(current),
            "cause": current.__cause__ is not None,
            "context_suppressed": suppress,
        })
        if current.__cause__:
            current = current.__cause__
        elif current.__context__ and not suppress:
            current = current.__context__
        else:
            break
    return chain


# ── Section 5: Custom exception hierarchy ────────────────────────────────────
class AppError(Exception):
    """Base for all application errors."""
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code

class ValidationError(AppError):
    pass

class AuthError(AppError):
    pass

class ResourceNotFoundError(AppError):
    pass


def process_request(user_id, data):
    if not isinstance(user_id, int):
        raise ValidationError(f"user_id must be int, got {type(user_id).__name__}", code=400)
    if user_id == 0:
        raise AuthError("Anonymous users not permitted", code=401)
    if user_id > 1000:
        raise ResourceNotFoundError(f"User {user_id} not found", code=404)
    return f"Processed for user {user_id}: {data}"


# ── Section 6: BaseException trap ────────────────────────────────────────────
def baseexception_trap():
    """Shows why you shouldn't catch BaseException in most cases."""
    import signal

    print("  Correct: except Exception catches app errors, not KeyboardInterrupt")
    try:
        raise ValueError("app error")
    except Exception as e:
        print(f"  Caught ValueError correctly: {e}")

    # demonstrate BaseException subclasses
    for exc_class in [KeyboardInterrupt, SystemExit, GeneratorExit]:
        is_exception_subclass = issubclass(exc_class, Exception)
        print(f"  issubclass({exc_class.__name__}, Exception) = {is_exception_subclass}")


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: Exception Chaining")
    print("=" * 55)

    # Section 1
    print("\n[1] Implicit chaining (raise inside except):")
    try:
        implicit_chain()
    except RuntimeError as e:
        print(f"  Caught: {type(e).__name__}: {e}")
        print(f"  __context__: {type(e.__context__).__name__}: {e.__context__}")
        print(f"  __cause__: {e.__cause__}  (None — no explicit from)")
        print(f"  __suppress_context__: {e.__suppress_context__}")

    # Section 2
    print("\n[2] Explicit chaining (raise X from Y):")
    try:
        explicit_chain()
    except DatabaseError as e:
        print(f"  Caught: {type(e).__name__}: {e}")
        print(f"  __cause__: {type(e.__cause__).__name__}: {e.__cause__}")
        print(f"  __suppress_context__: {e.__suppress_context__}  (True — explicit chain)")

    # Section 3
    print("\n[3] Suppressed chain (raise X from None):")
    try:
        suppressed_chain("my_key")
    except NotFoundError as e:
        print(f"  Caught: {type(e).__name__}: {e}")
        print(f"  __cause__: {e.__cause__}  (None — suppressed)")
        print(f"  __context__: {type(e.__context__).__name__}: {e.__context__}  (still stored)")
        print(f"  __suppress_context__: {e.__suppress_context__}  (True — won't display)")

    # Section 4
    print("\n[4] Walking the exception chain:")
    try:
        explicit_chain()
    except DatabaseError as e:
        chain = walk_chain(e)
        for i, entry in enumerate(chain):
            print(f"  [{i}] {entry['type']}: {entry['msg']!r}  cause={entry['cause']}")

    # Section 5
    print("\n[5] Custom exception hierarchy:")
    test_cases = [(0, {}), ("x", {}), (9999, {}), (42, {"action": "update"})]
    for uid, data in test_cases:
        try:
            result = process_request(uid, data)
            print(f"  user_id={uid!r}: OK → {result!r}")
        except AppError as e:
            print(f"  user_id={uid!r}: {type(e).__name__}(code={e.code}): {e}")

    # Section 6
    print("\n[6] BaseException trap:")
    baseexception_trap()

    print("\n[7] Formatted traceback of chained exception:")
    try:
        explicit_chain()
    except DatabaseError as e:
        lines = traceback.format_exception(type(e), e, e.__traceback__)
        # Show just the relevant lines
        for line in lines:
            for subline in line.splitlines():
                if subline.strip():
                    print(f"  {subline}")

    print("\n" + "=" * 55)
