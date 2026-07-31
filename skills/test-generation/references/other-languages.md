# JavaScript/TypeScript, Python, Go, Java

Secondary stacks — enough to write idiomatic tests and run them. Match the project's existing
suite over anything here.

## JavaScript / TypeScript

Detect the runner from `package.json` (`scripts.test`, devDependencies) before writing anything:
Vitest, Jest, `node:test`, Mocha, and Bun's runner all differ in imports and config.

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest';   // Jest: from '@jest/globals'

describe('formatPrice', () => {
  it('formats zero as free', () => {
    expect(formatPrice(0)).toBe('Free');
  });

  it('throws on negative amounts', () => {
    expect(() => formatPrice(-1)).toThrow(RangeError);
  });
});
```

- File placement: `src/foo.ts` → `src/foo.test.ts` (co-located) or `test/foo.test.ts` — follow the
  project; the runner's `include` glob decides what is discovered.
- `toBe` is identity, `toEqual` is structural, `toStrictEqual` also checks `undefined` keys and
  class identity. Choosing wrong produces tests that pass on the wrong value.
- Async: `await expect(p).resolves.toEqual(x)` / `.rejects.toThrow(x)`. Always `await` or `return`
  the assertion — an unawaited promise passes silently.
- Timers: `vi.useFakeTimers()` / `jest.useFakeTimers()` + `advanceTimersByTime`, never a real
  `setTimeout` wait. Restore in `afterEach`.
- Network: MSW (`msw`) intercepts at the network layer and is far more robust than mocking `fetch`.
- Module mocks (`vi.mock`, `jest.mock`) are hoisted — declare them at module top level, and prefer
  dependency injection over module mocking where the code allows it.
- React components: Testing Library (`render`, `screen.getByRole`, `userEvent`). Query by role and
  accessible name, never by CSS class or test-id-of-last-resort.

```bash
npx vitest run                         # CI mode, no watch
npx vitest run src/cart --reporter dot
npx jest --testPathPattern cart -t 'formats zero'
npm test -- --coverage                 # v8/istanbul; coverage/index.html
```

## Python

```python
import pytest
from cart import format_price

def test_formats_zero_as_free():
    assert format_price(0) == "Free"

def test_rejects_negative():
    with pytest.raises(ValueError, match="negative"):
        format_price(-1)

@pytest.mark.parametrize("amount,expected", [(0, "Free"), (1, "$1.00"), (1000, "$1,000.00")])
def test_formats(amount, expected):
    assert format_price(amount) == expected
```

- Files `test_*.py` (or `*_test.py`) under `tests/`, functions `test_*` — pytest discovers by name.
- Fixtures over `setUp`: `@pytest.fixture` with `yield` for teardown; `tmp_path`, `monkeypatch`,
  `caplog`, `capsys` are built in and remove most manual scaffolding.
- `monkeypatch.setattr` / `unittest.mock.patch` — patch **where it is used**, not where it is
  defined (`patch("mymodule.requests.get")`, not `patch("requests.get")`). This is the single most
  common patching mistake.
- Async: `pytest-asyncio` (`@pytest.mark.asyncio`) or `anyio`. Freeze time with `freezegun` or an
  injected clock.
- Property-based cases: `hypothesis` (`@given(st.text())`).

```bash
python -m pytest -q
python -m pytest tests/test_cart.py::test_rejects_negative
python -m pytest -q --cov=cart --cov-report=term-missing     # missing lines, not just a %
```

## Go

```go
func TestFormatPrice(t *testing.T) {
    tests := []struct {
        name string
        in   int
        want string
    }{
        {"zero is free", 0, "Free"},
        {"single unit", 1, "$1.00"},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := FormatPrice(tt.in)
            if err != nil {
                t.Fatalf("FormatPrice(%d) returned error: %v", tt.in, err)
            }
            if got != tt.want {
                t.Errorf("FormatPrice(%d) = %q, want %q", tt.in, got, tt.want)
            }
        })
    }
}
```

- Table-driven subtests are the Go idiom — write them that way even for two cases.
- `t.Errorf` continues, `t.Fatalf` stops. Message format: `got X, want Y`, with the input.
- `foo_test.go` beside `foo.go`, package `foo` (white-box) or `foo_test` (black-box, public API
  only). `t.Cleanup(...)` for teardown, `t.TempDir()` for files, `t.Parallel()` where safe.
- No mocking framework needed: accept interfaces, pass a struct that implements them.
  `httptest.NewServer` for HTTP, `testing/fstest` for filesystems.
- `TestMain` for suite-wide setup only when genuinely required.

```bash
go test ./...
go test -run TestFormatPrice ./cart
go test -race ./...                                  # run this on anything concurrent
go test -coverprofile=c.out ./... && go tool cover -html=c.out
```

## Java (plain JUnit)

```java
@Test
void rejectsNegativeAmounts() {
    var ex = assertThrows(IllegalArgumentException.class, () -> formatter.format(-1));
    assertEquals("amount must be non-negative", ex.getMessage());
}

@ParameterizedTest
@CsvSource({"0, Free", "1, $1.00"})
void formats(int amount, String expected) {
    assertEquals(expected, formatter.format(amount));
}
```

- JUnit 5 (`org.junit.jupiter.api`): `@Test`, `@BeforeEach`, `@Nested`, `@DisplayName`,
  `@ParameterizedTest`. `src/test/java` mirroring `src/main/java`.
- AssertJ (`assertThat(x).isEqualTo(y)`) reads better than raw JUnit assertions and is common.
- Mockito for doubles; `@ExtendWith(MockitoExtension.class)` + `@Mock`/`@InjectMocks`.
- `mvn test` / `gradle test`; JaCoCo for coverage. Filter Maven's output — it is verbose.
