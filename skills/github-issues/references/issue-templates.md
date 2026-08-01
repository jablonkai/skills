# Issue body templates

Every new issue MUST follow one of these structures. Pick the template that matches the issue type,
pre-fill "Summary" from context, and ask the user for any missing required section before creating.

## Title

- Start with a short, descriptive summary (max 72 characters)
- Use imperative mood: "Add ...", "Fix ...", "Update ...", "Remove ..."
- Do NOT prefix with type (no "Bug: ..." or "[Feature] ...") — labels handle categorization

## Enhancement / Feature template

```markdown
## Summary
<1-3 sentences describing what needs to happen and why>

## Proposed Solution
<Detailed description of the implementation approach. Include:>
- Affected files or modules (with paths where known)
- Sub-sections for distinct layers (e.g., ### Backend, ### Frontend)
- Code snippets or API signatures if relevant

## Additional context
<Links, screenshots, related issues, or implementation notes>
```

## Bug template

```markdown
## Summary
<1-3 sentences describing the bug and its impact>

## Current behavior
<What happens now — include error messages, stack traces, or logs>

## Expected behavior
<What should happen instead>

## Steps to reproduce
1. Step one
2. Step two
3. ...

## Proposed Solution
<Fix approach — which file/function to change and how>

## Additional context
<Links, screenshots, related issues>
```

## Rules

- "Summary" is always required — this is the primary section explaining what and why
- For bugs: "Current behavior", "Expected behavior", and "Steps to reproduce" are required
- "Proposed Solution" is strongly encouraged — include specific file paths, module names, and
  implementation details when known
- Use sub-headings (### Backend, ### Frontend, ### Flow) within "Proposed Solution" for complex
  changes touching multiple layers
- "Additional context" is optional but encouraged
- Remove unused sections rather than leaving them empty
- Reference concrete file paths and function/type names to make issues actionable

## Type detection from the title and context

- Bug indicators: "fix", "broken", "error", "crash", "fail", "wrong", "incorrect", "regression"
- Enhancement indicators: "add", "implement", "new", "improve", "show", "allow", "support", "enable"
- Documentation indicators: "document", "readme", "guide", "docs"
- If unclear, suggest `question`
