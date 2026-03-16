"""
Demo: copy & deepcopy — Python's Object Copying Protocol
Run:  python demo.py
"""
import copy
import threading

# ── Section 1: Shallow vs deep on nested structures ──────────────────────────
print("=" * 50)
print("Section 1: Shallow vs Deep")
print("=" * 50)

original = {"tags": ["a", "b"], "meta": {"score": 10}}
shallow  = copy.copy(original)
deep     = copy.deepcopy(original)

original["tags"].append("c")
original["meta"]["score"] = 99

print("original:", original)
print("shallow :", shallow)   # tags mutated, meta mutated — shared refs
print("deep    :", deep)      # fully independent

# ── Section 2: Custom __copy__ and __deepcopy__ ──────────────────────────────
print("\n" + "=" * 50)
print("Section 2: Custom Protocol")
print("=" * 50)

class Config:
    def __init__(self, settings: dict, conn=None):
        self.settings = settings
        self._conn    = conn       # non-copyable "resource"
        self._lock    = threading.Lock()

    def __copy__(self):
        new = Config.__new__(Config)
        new.settings = self.settings  # shallow — shared dict
        new._conn    = self._conn     # share the same connection
        new._lock    = threading.Lock()
        return new

    def __deepcopy__(self, memo):
        new = Config.__new__(Config)
        memo[id(self)] = new
        new.settings = copy.deepcopy(self.settings, memo)  # deep copy state
        new._conn    = None          # drop conn — must reconnect manually
        new._lock    = threading.Lock()
        return new

cfg        = Config({"timeout": 30, "hosts": ["a", "b"]}, conn="<DB>")
shallow_cfg = copy.copy(cfg)
deep_cfg    = copy.deepcopy(cfg)

cfg.settings["timeout"] = 999
cfg.settings["hosts"].append("c")

print("orig settings :", cfg.settings)
print("shallow       :", shallow_cfg.settings)  # timeout changed, hosts mutated
print("deep          :", deep_cfg.settings)     # fully isolated
print("deep conn     :", deep_cfg._conn)         # None — resource dropped

# ── Section 3: Cycle detection in deepcopy (memo dict) ───────────────────────
print("\n" + "=" * 50)
print("Section 3: Cycle detection")
print("=" * 50)

a = {}
b = {"ref": a}
a["ref"] = b           # cycle: a → b → a

clone = copy.deepcopy(a)
print("clone['ref']['ref'] is clone:", clone["ref"]["ref"] is clone)  # True — cycle preserved

# ── Section 4: What deepcopy does NOT copy ───────────────────────────────────
print("\n" + "=" * 50)
print("Section 4: Not copied (singletons, modules, functions)")
print("=" * 50)

import os
fn   = lambda x: x
none = None

print("fn copied?    ", copy.deepcopy(fn)   is fn)    # True — same object
print("None copied?  ", copy.deepcopy(None) is None)  # True
print("os copied?    ", copy.deepcopy(os)   is os)    # True

if __name__ == "__main__":
    print("\nAll sections complete.")
