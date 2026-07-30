# Rust and C / C++

## Rust — reading a panic

```
thread 'main' panicked at src/parser.rs:88:14:
index out of bounds: the len is 3 but the index is 5
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```

The panic header already gives file, line, column and the failing invariant — that is more than
most platforms provide. The backtrace matters only when the panic is inside a library and you
need the call path back into your code.

```bash
RUST_BACKTRACE=1 cargo run          # symbol names
RUST_BACKTRACE=full cargo run       # every frame, including std internals
```

Skip the `core::panicking::*`, `std::panicking::*` and `rust_begin_unwind` frames — the first
frame in your crate below them is the culprit.

## Rust — panic sources

| Panic message | Cause |
|---|---|
| `called Option::unwrap() on a None value` | Absent value assumed present; find the producer |
| `called Result::unwrap() on an Err value: <e>` | The `Err` payload *is* the diagnosis — read it, not the unwrap site |
| `index out of bounds` | Slice/Vec index from untrusted length arithmetic; prefer `.get()` |
| `attempt to subtract with overflow` | Unsigned underflow (debug builds panic, release wraps — a release-only bug is often this) |
| `already borrowed: BorrowMutError` | `RefCell` borrowed mutably while a shared borrow is live — usually a re-entrant call through a callback |
| `cannot recursively acquire mutex` / hang | `Mutex` re-locked on the same thread; `parking_lot` or a redesign |
| `called from async context` / blocking runtime | `block_on` or blocking I/O inside a Tokio worker — use `spawn_blocking` |
| `SIGSEGV` in a Rust binary | Almost always `unsafe` or an FFI boundary, not safe Rust |

## Rust — error chains

With `anyhow` / `thiserror` the useful information is in the chain, not the frame list:

```rust
// print the whole chain, not just the outermost message
eprintln!("{:#}", err);            // anyhow: all causes inline
eprintln!("{:?}", err);            // anyhow: causes + backtrace when RUST_BACKTRACE=1
for cause in err.chain() { … }     // walk it explicitly
```

- `thiserror` `#[from]` conversions preserve the source — check `.source()` recursively.
- An error that lost its context (a bare `io::Error: No such file or directory` with no path)
  means a `?` crossed a boundary without `.context("…")`. Adding context there is often the real fix.
- `RUST_BACKTRACE=1` also populates `anyhow`'s captured backtrace.

## Rust — FFI

- A panic unwinding across an `extern "C"` boundary is UB and aborts. Wrap the body in
  `std::panic::catch_unwind` at every FFI entry point.
- `SIGABRT` with `fatal runtime error: Rust cannot catch foreign exceptions` — a C++ exception
  crossed into Rust.
- Alignment, lifetime and null assumptions at the boundary are the usual UB sources; run the
  suite under Miri (`cargo +nightly miri test`) for the pure-Rust portion.

## C / C++ — crash classes

| Signal / report | Cause |
|---|---|
| `SIGSEGV` at a small address | Null pointer dereference (`0x0` + member offset) |
| `SIGSEGV` at a plausible address | Use-after-free, dangling reference, buffer overrun |
| `SIGABRT` | `assert()`, `std::terminate` (uncaught exception, exception in destructor), glibc heap corruption (`free(): invalid pointer`) |
| `SIGBUS` | Misaligned access, or mmap'd file truncated under you |
| `SIGILL` | Corrupted function pointer / vtable, or an instruction set mismatch |
| `SIGFPE` | Integer division by zero |
| Stack overflow (`SIGSEGV` with a huge frame count) | Unbounded recursion |

## C / C++ — get a real backtrace

```bash
ulimit -c unlimited            # enable core dumps first
gdb ./app core                 # then: bt full, info registers, frame N, list
lldb ./app -c core             # then: bt all, frame select N
addr2line -e ./app -f -C -i 0x4011a6    # single address, demangled, with inlined frames
```

Frames marked `<optimized out>` or with implausible arguments mean the build inlined them —
rebuild with `-O0 -g` to get a trustworthy trace before drawing conclusions.

## C / C++ — sanitizers beat traces

A crash report tells you where it died; a sanitizer tells you where the bug was introduced.
Reach for these before reading a raw core dump:

```bash
# AddressSanitizer — use-after-free, buffer overflow, leaks
clang++ -fsanitize=address -fno-omit-frame-pointer -g -O1 main.cpp

# UndefinedBehaviorSanitizer — signed overflow, bad shifts, null deref, misaligned access
clang++ -fsanitize=undefined -fno-sanitize-recover=all -g main.cpp

# ThreadSanitizer — data races (do not combine with ASan)
clang++ -fsanitize=thread -g main.cpp

valgrind --leak-check=full --track-origins=yes ./app   # slower, no rebuild needed
```

ASan output names both events — read them as a pair:

```
==1234==ERROR: AddressSanitizer: heap-use-after-free on address 0x60300000eff0
READ of size 4 at ... thread T0
    #0 0x4f1a2b in Widget::draw() widget.cpp:88     <- the use
freed by thread T0 here:
    #0 0x4c9d1a in operator delete(void*)
    #1 0x4f0e33 in Scene::clear() scene.cpp:31      <- the actual bug
```

The **free site**, not the read site, is normally what needs fixing.

## Android NDK

```bash
adb logcat | ndk-stack -sym <path-to-unstripped-libs>
```

`SIGSEGV` in a JNI frame usually means a stale `jobject` local reference used after the native
call returned, a missing `NewGlobalRef`, or a mismatch between the JNI signature string and the
actual Java method.
