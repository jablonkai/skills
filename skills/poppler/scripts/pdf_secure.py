#!/usr/bin/env python3
"""Passwords, linearisation and repair with qpdf, each output verified.

  pdf_secure.py encrypt   IN OUT --user-password-file F [--owner-password-file F] [--no-print] [--no-modify] [--no-copy]
  pdf_secure.py decrypt   IN OUT --password-file F [--compare-to ORIGINAL.pdf]
  pdf_secure.py linearize IN OUT
  pdf_secure.py repair    IN OUT

Passwords come from a file (first line) or an environment variable (--*-password-env),
never from argv. encrypt uses AES-256; without an owner password a random one is
generated and written next to OUT as OUT.owner-password.txt (mode 0600).
Exit 0 verified, 1 verification failed, 2 usage/tool error, 4 wrong password.
"""
import argparse
import os
import secrets
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdfcommon import (add_password_args, check, die, emit, is_encrypted, needs_password, norm,  # noqa: E402
                       page_count, qpdf, read_password, readable, text_pages)


def text_of(path, password=None):
    with readable(path, password) as p:
        return [norm(t) for t in text_pages(p, range(1, page_count(p) + 1), "plain")]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("encrypt")
    add_password_args(e, "user-", "user (open) password")
    add_password_args(e, "owner-", "owner (permissions) password")
    e.add_argument("--no-print", action="store_true")
    e.add_argument("--no-modify", action="store_true")
    e.add_argument("--no-copy", action="store_true", help="disallow text/image extraction")
    d = sub.add_parser("decrypt")
    add_password_args(d)
    d.add_argument("--compare-to", metavar="PDF", help="unencrypted original to compare text and pages with")
    lin = sub.add_parser("linearize")
    rep = sub.add_parser("repair")
    for p in (lin, rep):
        add_password_args(p)
    for p in sub.choices.values():
        p.add_argument("inp")
        p.add_argument("out")
    a = ap.parse_args()
    if os.path.abspath(a.inp) == os.path.abspath(a.out):
        die("output would overwrite the input; write to a new file")
    if not os.path.exists(a.inp):
        die(f"no such file: {a.inp}")

    if a.cmd == "encrypt":
        user = read_password(a.user_password_file, a.user_password_env, required=True, label="user password")
        owner = read_password(a.owner_password_file, a.owner_password_env)
        owner_file = None
        if not owner:
            owner = secrets.token_urlsafe(18)
            owner_file = a.out + ".owner-password.txt"
            fd = os.open(owner_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as fh:
                fh.write(owner + "\n")
        if owner == user:
            die("owner password equals the user password: anyone who can open the file gets full permissions")
        restrict = []
        if a.no_print:
            restrict.append("--print=none")
        if a.no_modify:
            restrict.append("--modify=none")
        if a.no_copy:
            restrict.append("--extract=n")
        src_pages = page_count(a.inp)
        qpdf([a.inp, "@SECRET", a.out],
             ["--encrypt", f"--user-password={user}", f"--owner-password={owner}", "--bits=256", *restrict, "--"],
             fatal=True)
        enc = qpdf(["--show-encryption", "@SECRET", a.out], [f"--password={user}"]).stdout
        report = {
            "output": a.out,
            "encrypted": is_encrypted(a.out),
            "opens_without_password": not needs_password(a.out),
            "aes256": "AESv3" in enc or "R = 6" in enc,
            "pages": page_count(a.out, user), "expected_pages": src_pages,
            "check": check(a.out, user)["status"],
            "restrictions": restrict,
            "owner_password_file": owner_file,
        }
        report["ok"] = (report["encrypted"] and not report["opens_without_password"] and report["aes256"]
                        and report["pages"] == src_pages and report["check"] != "errors")

    elif a.cmd == "decrypt":
        pw = read_password(a.password_file, a.password_env)
        if not is_encrypted(a.inp):
            die(f"{a.inp} is not encrypted")
        if needs_password(a.inp) and pw is None:
            die("this file needs its user password: pass --password-file or --password-env", 4)
        proc = qpdf(["--decrypt", "@SECRET", a.inp, a.out], [f"--password={pw or ''}"])
        if proc.returncode == 2 or not os.path.exists(a.out):
            die(f"decrypt failed (wrong password?): {proc.stderr.strip()[:200]}", 4)
        report = {"output": a.out, "encrypted": is_encrypted(a.out), "pages": page_count(a.out),
                  "expected_pages": page_count(a.inp, pw), "check": check(a.out)["status"]}
        ok = not report["encrypted"] and report["pages"] == report["expected_pages"] and report["check"] != "errors"
        same = text_of(a.out) == text_of(a.inp, pw)
        report["text_identical_to_input"] = same
        ok = ok and same
        if a.compare_to:
            orig = text_of(a.compare_to)
            report["text_identical_to_original"] = text_of(a.out) == orig
            report["pages_match_original"] = page_count(a.compare_to) == report["pages"]
            ok = ok and report["text_identical_to_original"] and report["pages_match_original"]
        report["ok"] = ok

    elif a.cmd == "linearize":
        pw = read_password(a.password_file, a.password_env)
        qpdf(["--linearize", "@SECRET", a.inp, a.out], [f"--password={pw}"] if pw else None, fatal=True)
        lin = qpdf(["--check-linearization", "@SECRET", a.out], [f"--password={pw}"] if pw else None)
        report = {"output": a.out, "linearized": lin.returncode == 0 and "no linearization errors" in lin.stdout,
                  "pages": page_count(a.out, pw), "expected_pages": page_count(a.inp, pw),
                  "check": check(a.out, pw)["status"]}
        report["ok"] = report["linearized"] and report["pages"] == report["expected_pages"] and report["check"] == "ok"

    else:  # repair
        pw = read_password(a.password_file, a.password_env)
        before = check(a.inp, pw)
        proc = qpdf(["@SECRET", a.inp, a.out], [f"--password={pw}"] if pw else None)
        if not os.path.exists(a.out):
            die(f"qpdf could not rebuild the file: {proc.stderr.strip()[:400]}")
        after = check(a.out, pw)
        report = {"output": a.out, "input_check": before["status"], "input_messages": before["messages"],
                  "repair_warnings": proc.stderr.strip().splitlines()[:10],
                  "output_check": after["status"], "pages": page_count(a.out, pw)}
        try:
            with readable(a.inp, pw) as p_in:
                text_in = [norm(t) for t in text_pages(p_in, range(1, page_count(a.out, pw) + 1), "plain")]
            report["text_identical_to_input"] = text_of(a.out, pw) == text_in
        except SystemExit:
            report["text_identical_to_input"] = None  # poppler could not read the damaged input
        report["ok"] = after["status"] == "ok"

    emit(report)
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
