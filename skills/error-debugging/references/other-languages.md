# Secondary platforms — Python, JavaScript/TypeScript, Go, Java

These come up occasionally. Depth here is deliberately shallower than the primary-stack
references; the workflow in `SKILL.md` still applies unchanged.

## Python

```
Traceback (most recent call last):
  File "app/main.py", line 12, in <module>
    run()
  File "app/service.py", line 88, in run
    return payload["items"][0]
KeyError: 'items'
```

- Python traces read **top-down**: the last frame is where it threw.
- `During handling of the above exception, another exception occurred` — the second block is what
  actually escaped; the first is what triggered the handler. `The above exception was the direct
  cause` (from `raise … from e`) means the first block is the root cause.
- Common: `KeyError`/`AttributeError` on an assumed-shaped dict or `None`; `TypeError: NoneType`
  from a function that returns `None` on a branch; `ImportError` from a circular import;
  `UnboundLocalError` from assigning to a name that also reads a global.
- Async: `RuntimeError: Event loop is closed`, `Task was destroyed but it is pending` — a task not
  awaited before shutdown. `asyncio.gather(..., return_exceptions=True)` silently collects errors.
- `python -X faulthandler` (or `faulthandler.enable()`) dumps a trace on segfault/hang;
  `PYTHONBREAKPOINT`, `pdb.post_mortem()`, and `pytest --tb=long -x` narrow it down.

## JavaScript / TypeScript

- Traces read top-down; frames after an `await` lose the synchronous caller unless
  `--async-stack-traces` (default in modern V8) applies.
- `TypeError: Cannot read properties of undefined (reading 'x')` — the object, not `x`, is the
  problem; find where it should have been assigned.
- `UnhandledPromiseRejection` — a promise without a `.catch`/`try`. In Node 15+ this terminates
  the process; register `process.on('unhandledRejection')` to log the origin.
- `ERR_MODULE_NOT_FOUND` / `require is not defined` — ESM/CJS mismatch, not a code bug.
- Minified browser traces need source maps (`//# sourceMappingURL`) — map before analyzing.
- `Maximum call stack size exceeded` — unbounded recursion, often a getter/proxy loop or a
  circular JSON structure.
- TypeScript types vanish at runtime: a value that "cannot" be undefined per the types usually
  came from an unvalidated API boundary or an `as` cast.

## Go

```
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x4a1b2c]

goroutine 1 [running]:
main.(*Server).handle(0x0, ...)
        /app/server.go:88 +0x2c
```

- Every goroutine's stack is dumped; the one marked `[running]` panicked. Others show their state
  (`[chan receive]`, `[select]`, `[semacquire]`) — invaluable for deadlocks.
- `nil pointer dereference` — a nil receiver or an unchecked error return that left a value nil.
- `all goroutines are asleep - deadlock!` — unbuffered channel with no counterpart, or a `WaitGroup`
  whose `Done` is never reached.
- `concurrent map writes` / `concurrent map read and map write` — fatal, not recoverable; use
  `sync.Map` or a mutex. Confirm with `go test -race ./...`.
- `context deadline exceeded` — usually correct behaviour surfacing an upstream slowness, not a bug
  at the frame shown.

## Java (non-Android)

Same trace grammar as the Kotlin/JVM reference — see
[kotlin-android-kmp.md](kotlin-android-kmp.md) for `Caused by:` chains, suppressed exceptions,
and the common exception table. Java-specific additions:

- `NoClassDefFoundError` vs `ClassNotFoundException` — the former means the class failed to
  *initialize* (look for the earlier `ExceptionInInitializerError`), the latter that it is absent
  from the classpath.
- `NoSuchMethodError` / `AbstractMethodError` — binary incompatibility between compile-time and
  runtime dependency versions; check the dependency tree for a conflicting version.
- `OutOfMemoryError: Metaspace` vs `Java heap space` vs `GC overhead limit exceeded` are three
  different problems; take a heap dump (`-XX:+HeapDumpOnOutOfMemoryError`) for the heap ones.
- `jstack <pid>` for a live thread dump; `jcmd <pid> Thread.print` is the modern equivalent.
