# Static-analysis tooling by stack

Run only what the project already configures or what is installed on the machine — never
install a tool or a dependency to make one of these work. Prefer machine-readable output
and filter it down; never paste a full log into the report.

## Contents

- [General rules](#general-rules)
- [Per-stack commands](#per-stack-commands)
- [Stack-agnostic checks](#stack-agnostic-checks)

## General rules

- **Configured beats available.** A linter wired into CI or a pre-commit hook reflects the
  team's standards; running an unconfigured linter with default rules produces style noise
  the project never agreed to. Use unconfigured tools only for high-signal rule sets
  (security, vulnerability databases, compiler warnings).
- **Keep output small.** Pipe through `tail`, `grep`, `jq`, or a count. What goes into the
  report is a summary ("ruff: 41 findings, 3 of them `S` security rules — see SEC-02"),
  not the raw output.
- **Watch for side effects.** Some commands build the project or resolve dependencies.
  Skip anything that would trigger a large first-time download (a Gradle wrapper
  distribution, a cold `cargo` registry, `pod install`) and say so under *What was NOT
  analyzed*. Network-only checks (`npm audit`, `pip-audit`, `dart pub outdated`) are fine
  when they don't write to the tree.
- **Bound the runtime.** If a command is still running after a few minutes, stop it and
  record that it was skipped rather than stalling the audit.

## Per-stack commands

| Stack | Commands |
|-------|----------|
| JS / TS | `npm audit --json`, `npx --no-install eslint . --format json`, `npx --no-install tsc --noEmit` |
| Python | `pip-audit`, `ruff check . --output-format json`, `mypy .`, `bandit -r . -f json -q` |
| Go | `go vet ./...`, `staticcheck ./...`, `govulncheck ./...` |
| Rust | `cargo clippy --message-format short -- -D warnings`, `cargo audit` |
| Dart / Flutter | `flutter analyze` (or `dart analyze`), `dart pub outdated` |
| Kotlin / Android / KMP | `./gradlew --console=plain --offline lint detekt ktlintCheck` — run only the tasks that exist (`./gradlew --offline tasks --all \| grep -E 'lint\|detekt\|ktlint'`) |
| Swift / iOS / macOS | `swiftlint lint --reporter json`, `xcodebuild -quiet analyze -scheme <scheme>` (only when the scheme is obvious) |
| C / C++ | `clang-tidy` with the project's `compile_commands.json`, `cppcheck --enable=warning,performance --quiet .` |
| Java | `./gradlew --console=plain --offline check` or `mvn -q -o verify -DskipTests` |
| Ruby | `bundle exec rubocop --format json`, `bundle exec brakeman -q` (Rails) |
| PHP | `composer audit`, `vendor/bin/phpstan analyse --no-progress` |

`npx --no-install` makes `npx` fail instead of silently downloading a package.

## Stack-agnostic checks

- Secrets: `gitleaks detect --no-banner`, `trufflehog filesystem . --no-update`. Without
  either, grep for common key shapes:
  `git grep -nIE '(AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[baprs]-|ghp_[0-9A-Za-z]{36}|sk_live_)'`
- Secrets in history (small repos only):
  `git log -p --all | grep -nE '(AKIA[0-9A-Z]{16}|PRIVATE KEY-----)' | head`
- Markers of known debt: `git grep -nE "TODO|FIXME|HACK|XXX" | wc -l`, then read the
  ones in critical paths.
- Hotspots: `git log --since="6 months ago" --name-only --pretty=format: | sort | uniq -c | sort -rn | head -20`
