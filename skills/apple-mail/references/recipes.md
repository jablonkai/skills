# Recipes

`S` is the skill's `scripts/` directory.

## Who wrote to me this month, and how much
```bash
python3 $S/mail-search.py --since 30d --account Google --count-by sender | head -20
```

## Receipts and invoices into a folder
```bash
python3 $S/mail-search.py --from billing@acme.test --since 2026-01-01 --has-attachment   # check the set
python3 $S/mail-export.py --from billing@acme.test --since 2026-01-01 --attachments-only \
  --match-attachment .pdf --out ~/Documents/Invoices/Acme
python3 $S/mail-verify.py export --dir ~/Documents/Invoices/Acme
```
Name clashes become `invoice-2.pdf`; `manifest.json` maps every file to its message.

## Reply to "the latest mail from X about Y", with a file
```bash
python3 $S/mail-search.py --from anna@lease.test --subject lease --limit 3 --json > hits.json
# pick the newest one that is really about Y (hits are newest first), then:
python3 $S/mail-draft.py --reply-to "<ref>" --body-file reply.txt --attach ~/contract.pdf
```
Tell the user the draft is in Drafts and that they send it.

## Newsletter cleanup
```bash
python3 $S/mail-organize.py archive --newsletter --before 90d --mailbox "Google/INBOX"        # preview
python3 $S/mail-organize.py archive --newsletter --before 90d --mailbox "Google/INBOX" --yes
```
For a different target: `--dest "On My Mac/Newsletters"`. Flags and read state are kept.

## Flag mail from someone
```bash
python3 $S/mail-organize.py flag --color red --from boss@corp.test --since 7d --yes
```

## Export a thread to Markdown
```bash
python3 $S/mail-search.py --subject "Project Kestrel" --since 6m --json > thread.json
python3 $S/mail-export.py --ids-from thread.json --format md --out ~/Notes/kestrel
```

## Unread overview
```bash
bash $S/mail.sh mailboxes --counts | grep -v ' 0 unread'
```
