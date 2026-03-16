# Bytecode & the dis Module — CPython Internals

## 🎯 Interview Question
What is Python bytecode, how does CPython execute it, and how would you use the `dis` module to diagnose a performance issue or understand a confusing scoping behavior?

## 💡 Short Answer (30 seconds)
Python source is compiled to bytecode — a sequence of 2-byte instructions (opcode + argument) stored in `.pyc` files and `code` objects. CPython's eval loop (`ceval.c`) executes them on a stack-based virtual machine. The `dis` module disassembles bytecode to human-readable opcodes, letting you see *exactly* how Python resolves names, builds closures, calls functions, and what the compiler optimizes away.

## 🔬 Deep Explanation
**Compilation pipeline:**
```
.py → tokenizer → AST → symbol table → bytecode (code object) → .pyc
```
`compile(source, '<string>', 'exec')` exposes the whole pipeline.

**Code object (`types.CodeType`) key attributes:**
- `co_code` — raw bytecode bytes (Python < 3.11) / `co_code` deprecated in 3.12+
- `co_consts` — constant pool (literals)
- `co_varnames` — local variable names
- `co_freevars` — variables captured from enclosing scopes (cell vars)
- `co_stacksize` — max stack depth needed
- `co_flags` — bitmask: OPTIMIZED, NEWLOCALS, VARARGS, VARKEYWORDS, GENERATOR, COROUTINE, ASYNC_GENERATOR

**Key opcodes to know:**
| Opcode | Meaning |
|---|---|
| `LOAD_FAST` | Load local variable from `co_varnames` |
| `LOAD_GLOBAL` | Load from global/built-in dict |
| `LOAD_DEREF` | Load from closure cell |
| `LOAD_CONST` | Push constant from `co_consts` |
| `CALL_FUNCTION` | Call with positional args (< 3.11) |
| `CALL` | Universal call (3.11+) |
| `BUILD_LIST` | Pop N items, build list |
| `LIST_APPEND` | Used in list comprehension |
| `MAKE_FUNCTION` | Create function object |
| `RETURN_VALUE` | Return TOS to caller |

**Peephole optimizations (compile-time):**
- Constant folding: `"ab" + "cd"` → `"abcd"` at compile time.
- Dead code elimination: unreachable `if False:` blocks removed.
- Jump optimization: chains of jumps collapsed.

**Why this matters in interviews:**
- Explains why `"hello" is "hello"` works (constant interning).
- Explains LEGB: `LOAD_FAST` vs `LOAD_GLOBAL` vs `LOAD_DEREF`.
- Explains why `+=` on a list inside a function before assignment raises `UnboundLocalError`.

## 💻 Code Example
```python
import dis

def add(a, b):
    return a + b

dis.dis(add)
# LOAD_FAST 'a'
# LOAD_FAST 'b'
# BINARY_OP  +
# RETURN_VALUE
```

## ⚠️ Common Mistakes & Interview Traps
- **`UnboundLocalError` trap**: assigning to a variable *anywhere* in a function makes it `LOAD_FAST` (local) *throughout* — even lines before the assignment.
- **Constant folding is not guaranteed for all expressions**: `x = 1 + 2` folds to 3; `x = int("1") + 2` does not.
- **`co_code` is deprecated** in Python 3.12+; use `co_code_bytes` or iterate `dis.get_instructions()`.
- **Bytecode is version-specific**: `.pyc` from Python 3.11 cannot run on 3.10.

## 🔗 Related Concepts
- python_core/036_closure_cells — LOAD_DEREF explains closure mechanics
- python_core/008_generators_internals — generator frame suspension at YIELD_VALUE
- python_core/004_metaclasses — `compile()` and code objects

## 📚 Go Deeper
- `dis.get_instructions()` — iterate over `Instruction` namedtuples
- CPython `Python/ceval.c` — the main eval loop (`_PyEval_EvalFrameDefault`)
