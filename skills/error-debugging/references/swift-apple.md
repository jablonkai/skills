# Swift — iOS / macOS

## Reading an Apple crash report

`.ips` (JSON header + text body) and legacy `.crash` files share the same anatomy. Read in this order:

1. **`Exception Type` / `Termination Reason`** — what kind of death
2. **`Triggered by Thread`** — which thread block to actually read
3. **That thread's frames** — topmost app-binary frame is your code
4. **`Binary Images`** — the UUID needed for symbolication

```
Exception Type:  EXC_BAD_ACCESS (SIGSEGV)
Exception Subtype: KERN_INVALID_ADDRESS at 0x0000000000000010
Triggered by Thread:  0

Thread 0 Crashed:
0   MyApp    0x1045a2b1c  ProfileViewModel.load()  (ProfileViewModel.swift:42)
```

## Exception types

| Type | Meaning |
|---|---|
| `EXC_BAD_ACCESS (SIGSEGV/SIGBUS)` | Dereferenced freed, nil, or misaligned memory. Address near `0x0`–`0x10` = nil/uninitialized; a large plausible address = use-after-free (zombie object) |
| `EXC_BREAKPOINT (SIGTRAP)` | Swift runtime trap: force-unwrap of nil, array index out of range, integer overflow, forced `try`, precondition failure |
| `EXC_CRASH (SIGABRT)` | Uncaught Objective-C exception, `fatalError()`, assertion, or an `abort()` from a system library |
| `EXC_RESOURCE` | Exceeded CPU or memory limit — the watchdog, not a logic bug in the frame shown |
| `Termination Reason: … 0x8badf00d` | Watchdog: main thread blocked too long (launch or resume timeout) |
| `Namespace SPRINGBOARD, Code 0x8badf00d` | Same watchdog, during app lifecycle transitions |
| `EXC_GUARD` | Misused file descriptor / guarded resource, often a double-close |

## Swift-specific traps

`EXC_BREAKPOINT` frames name the trap in the symbol when symbolicated:

- `Swift runtime failure: Unexpectedly found nil while unwrapping an Optional value` — a `!` or an
  implicitly-unwrapped optional (IBOutlet accessed before load, or after teardown)
- `Fatal error: Index out of range` — array bounds; find who produced the index
- `Fatal error: Unexpectedly found nil` in a `guard`-less initializer path
- `Swift runtime failure: arithmetic overflow` — unchecked `Int` math on untrusted input
- `Fatal error: Duplicate keys / Dictionary key must be unique` — `Dictionary(uniqueKeysWithValues:)` on non-unique input

## Concurrency

- **Main-actor violations**: UIKit/AppKit touched off the main thread. Under Swift 6 strict
  concurrency this is a compile error; in older code it shows as `EXC_BAD_ACCESS` deep inside
  UIKit with no obvious cause. Check `Thread 0` vs the crashing thread — a UIKit frame on a
  non-zero thread is the tell.
- **Data race**: enable the Thread Sanitizer (`Scheme → Diagnostics → Thread Sanitizer`); TSan
  reports both the racing accesses, which the crash report cannot.
- **Actor reentrancy**: state read before an `await` may be stale after it. A crash after an
  `await` on state that "cannot" be nil is usually this.
- **Task cancellation**: `CancellationError` thrown from `Task.checkCancellation()` propagating
  into a `try!` — check that cancellation is handled, not force-tried.
- **Deadlock**: `dispatch_sync` onto the current queue, or `DispatchSemaphore.wait()` on the main
  thread. Shows up as an `0x8badf00d` watchdog termination, not an exception.

## Memory

- **Retain cycles** do not crash directly; they cause growth and use-after-dealloc when a
  `[weak self]` was expected. Use the Memory Graph Debugger and Instruments' Leaks.
- **Zombies**: enable `NSZombieEnabled` (scheme diagnostics) to turn "message sent to deallocated
  instance" from a garbage `EXC_BAD_ACCESS` into a named error.
- **`EXC_RESOURCE (MEMORY)`** — jetsam; look at peak memory, not the crashing frame. Image decode
  and video buffers dominate.

## Objective-C exceptions

```
*** Terminating app due to uncaught exception 'NSInvalidArgumentException',
    reason: '-[__NSCFString count]: unrecognized selector sent to instance 0x600002...'
```

- `unrecognized selector` — wrong type at a dynamic boundary (JSON, KVC, storyboard outlet,
  NSCoding). The class named in the message is what you *actually* have.
- `NSRangeException` — bounds on `NSArray`/`NSString` from bridged Swift code.
- `NSInternalInconsistencyException` from `UITableView` — the data-source count does not match
  the batch update you performed.
- Add an exception breakpoint (`Breakpoint navigator → + → Exception Breakpoint`) to stop at the
  throw rather than at the terminate.

## Symbolication

Frames with hex addresses only need the dSYM matching the crashing build's UUID — see
[symbolication.md](symbolication.md). Swift symbols may still appear mangled (`$s5MyApp...`);
demangle with `xcrun swift-demangle`.

## Useful commands

```bash
xcrun swift-demangle '$s5MyApp16ProfileViewModelC4loadyyF'
xcrun simctl spawn booted log stream --predicate 'process == "MyApp"'   # simulator logs
log show --last 10m --predicate 'process == "MyApp"'                    # macOS logs
xcodebuild test -scheme MyApp -destination 'platform=iOS Simulator,name=iPhone 15'
```
