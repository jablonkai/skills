// EventKit helper for the apple-reminders skill: one command per run, JSON out on stdout.
//
//   ek status                                  authorization state, no prompt
//   ek lists                                   every reminder list
//   ek query open|all [LIST_ID ...]            open (or all) reminders, undated included
//   ek query completed FROM|- TO|- [LIST_ID ...]   completed in [FROM, TO)
//   ek get ID [ID ...]                         reminders by id (missing ids are left out)
//   ek save < spec.json                        create or update one spec or an array, then read back
//   ek delete ID [ID ...]                      remove reminders
//   ek newlist TITLE [SOURCE_TITLE]            create a list (default: the default list's account)
//
// Dates are ISO 8601 with an offset (2026-10-20T10:00:00+02:00) or a bare date
// (2026-10-20). A bare due date makes an all-day reminder. Output dates carry the local
// offset; an all-day due date is output as YYYY-MM-DD with "allDay": true.
// Exit codes: 0 ok, 2 bad input or not found, 3 no reminders access, 1 EventKit error.
import EventKit
import Foundation

let store = EKEventStore()
let cal = Calendar.current
let iso: ISO8601DateFormatter = {
    let f = ISO8601DateFormatter()
    f.formatOptions = [.withInternetDateTime]
    f.timeZone = TimeZone.current
    return f
}()
let isoFrac: ISO8601DateFormatter = {
    let f = ISO8601DateFormatter()
    f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
    return f
}()
let dayFmt: DateFormatter = {
    let f = DateFormatter()
    f.locale = Locale(identifier: "en_US_POSIX")
    f.dateFormat = "yyyy-MM-dd"
    f.timeZone = TimeZone.current
    return f
}()

func fail(_ msg: String, _ code: Int32 = 1) -> Never {
    FileHandle.standardError.write(("error: " + msg + "\n").data(using: .utf8)!)
    exit(code)
}

func emit(_ obj: Any) {
    guard let data = try? JSONSerialization.data(withJSONObject: obj, options: [.prettyPrinted, .sortedKeys]) else {
        fail("could not encode output")
    }
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write("\n".data(using: .utf8)!)
}

func parseDate(_ s: String) -> Date {
    if let d = iso.date(from: s) ?? isoFrac.date(from: s) ?? dayFmt.date(from: s) { return d }
    fail("bad date \(s) (want 2026-10-20T10:00:00+02:00 or 2026-10-20)", 2)
}

let statusNames: [EKAuthorizationStatus: String] = [
    .notDetermined: "notDetermined", .restricted: "restricted", .denied: "denied",
    .fullAccess: "fullAccess", .writeOnly: "writeOnly",
]

func authStatus() -> String { statusNames[EKEventStore.authorizationStatus(for: .reminder)] ?? "unknown" }

// Ask once when undecided; afterwards only System Settings can change the answer.
// The prompt appears only for a compiled binary, not under `swift script.swift`.
func requireAccess() {
    var st = EKEventStore.authorizationStatus(for: .reminder)
    if st == .notDetermined {
        let sem = DispatchSemaphore(value: 0)
        store.requestFullAccessToReminders { _, _ in sem.signal() }
        sem.wait()
        st = EKEventStore.authorizationStatus(for: .reminder)
    }
    if st == .fullAccess { return }
    fail("reminders access is \(statusNames[st] ?? "unknown"): turn on access for this terminal/IDE in "
        + "System Settings > Privacy & Security > Reminders, then retry", 3)
}

// ---- encoding ----------------------------------------------------------------

let freqNames: [EKRecurrenceFrequency: String] = [.daily: "DAILY", .weekly: "WEEKLY", .monthly: "MONTHLY", .yearly: "YEARLY"]
let freqValues: [String: EKRecurrenceFrequency] = ["DAILY": .daily, "WEEKLY": .weekly, "MONTHLY": .monthly, "YEARLY": .yearly]

func ruleString(_ r: EKRecurrenceRule) -> String {
    var parts = ["FREQ=\(freqNames[r.frequency] ?? "DAILY")"]
    if r.interval > 1 { parts.append("INTERVAL=\(r.interval)") }
    if let end = r.recurrenceEnd {
        if end.occurrenceCount > 0 {
            parts.append("COUNT=\(end.occurrenceCount)")
        } else if let d = end.endDate {
            parts.append("UNTIL=" + dayFmt.string(from: d))
        }
    }
    return parts.joined(separator: ";")
}

func isAllDay(_ c: DateComponents) -> Bool { c.hour == nil }

func dueString(_ c: DateComponents) -> String? {
    if isAllDay(c) {
        guard let y = c.year, let m = c.month, let d = c.day else { return nil }
        return String(format: "%04d-%02d-%02d", y, m, d)
    }
    var cc = c
    if cc.timeZone == nil { cc.timeZone = TimeZone.current }  // floating time = local
    guard let date = cal.date(from: cc) else { return nil }
    return iso.string(from: date)
}

func listDict(_ c: EKCalendar) -> [String: Any] {
    [
        "id": c.calendarIdentifier,
        "title": c.title,
        "source": c.source?.title ?? "",
        "writable": c.allowsContentModifications,
        "default": c.calendarIdentifier == store.defaultCalendarForNewReminders()?.calendarIdentifier,
    ]
}

let priorityNames: [Int: String] = [0: "none", 1: "high", 5: "medium", 9: "low"]

func reminderDict(_ r: EKReminder) -> [String: Any] {
    var d: [String: Any] = [
        "id": r.calendarItemIdentifier,
        "title": r.title ?? "",
        "list": r.calendar?.title ?? "",
        "listId": r.calendar?.calendarIdentifier ?? "",
        "source": r.calendar?.source?.title ?? "",
        "completed": r.isCompleted,
        "priority": r.priority,
        "priorityName": priorityNames[r.priority] ?? (r.priority < 5 ? "high" : r.priority == 5 ? "medium" : "low"),
        "notes": r.notes ?? "",
        "url": r.url?.absoluteString ?? "",
        "allDay": false,
        "alarms": (r.alarms ?? []).map { a -> [String: Any] in
            if let ad = a.absoluteDate { return ["absolute": iso.string(from: ad)] }
            return ["offsetMinutes": Int((a.relativeOffset / 60).rounded())]
        },
        "repeat": (r.recurrenceRules ?? []).map(ruleString).first ?? "",
    ]
    if let c = r.dueDateComponents, let s = dueString(c) {
        d["due"] = s
        d["allDay"] = isAllDay(c)
    } else {
        d["due"] = NSNull()
    }
    d["completionDate"] = r.completionDate.map { iso.string(from: $0) as Any } ?? NSNull()
    d["created"] = r.creationDate.map { iso.string(from: $0) as Any } ?? NSNull()
    d["modified"] = r.lastModifiedDate.map { iso.string(from: $0) as Any } ?? NSNull()
    return d
}

// ---- lookups ------------------------------------------------------------------

func reminderLists() -> [EKCalendar] { store.calendars(for: .reminder) }

func listsById(_ ids: [String]) -> [EKCalendar]? {
    if ids.isEmpty { return nil }
    let all = reminderLists()
    return ids.map { id in
        guard let c = all.first(where: { $0.calendarIdentifier == id }) else { fail("no reminder list with id \(id)", 2) }
        return c
    }
}

func fetch(_ p: NSPredicate) -> [EKReminder] {
    let sem = DispatchSemaphore(value: 0)
    var out: [EKReminder] = []
    store.fetchReminders(matching: p) { r in
        out = r ?? []
        sem.signal()
    }
    sem.wait()
    return out
}

func reminder(_ id: String) -> EKReminder {
    let bare = id.replacingOccurrences(of: "x-apple-reminder://", with: "")
    guard let r = store.calendarItem(withIdentifier: bare) as? EKReminder else { fail("no reminder with id \(id)", 2) }
    return r
}

// ---- save ---------------------------------------------------------------------

func components(for s: String) -> DateComponents {
    if s.count == 10, let d = dayFmt.date(from: s) {
        return cal.dateComponents([.year, .month, .day], from: d)
    }
    var c = cal.dateComponents([.year, .month, .day, .hour, .minute, .second], from: parseDate(s))
    c.timeZone = TimeZone.current
    return c
}

func apply(_ spec: [String: Any]) -> EKReminder {
    let r: EKReminder
    if let id = spec["id"] as? String {
        r = reminder(id)
    } else {
        r = EKReminder(eventStore: store)
        guard spec["title"] is String else { fail("a new reminder needs a title", 2) }
        if spec["list"] == nil {
            guard let def = store.defaultCalendarForNewReminders() else { fail("no default reminder list", 2) }
            r.calendar = def
        }
    }
    if let lid = spec["list"] as? String { r.calendar = listsById([lid])![0] }
    if !(r.calendar?.allowsContentModifications ?? false) { fail("list \(r.calendar?.title ?? "?") is read-only", 2) }
    if let t = spec["title"] as? String { r.title = t }
    if let v = spec["notes"] { r.notes = v as? String }
    if let v = spec["url"] { r.url = (v as? String).flatMap { $0.isEmpty ? nil : URL(string: $0) } }
    if let p = spec["priority"] as? Int { r.priority = p }
    if let v = spec["due"] {
        if let s = v as? String { r.dueDateComponents = components(for: s) } else { r.dueDateComponents = nil }
    }
    if let v = spec["alarms"] {
        for a in r.alarms ?? [] { r.removeAlarm(a) }
        for a in (v as? [[String: Any]]) ?? [] {
            if let s = a["absolute"] as? String {
                r.addAlarm(EKAlarm(absoluteDate: parseDate(s)))
            } else if let m = a["offsetMinutes"] as? Int {
                r.addAlarm(EKAlarm(relativeOffset: TimeInterval(m * 60)))
            }
        }
    }
    if let v = spec["repeat"] {
        for rule in r.recurrenceRules ?? [] { r.removeRecurrenceRule(rule) }
        if let rr = v as? [String: Any], let f = rr["freq"] as? String {
            guard let freq = freqValues[f.uppercased()] else { fail("bad repeat frequency \(f)", 2) }
            guard r.dueDateComponents != nil else { fail("a repeating reminder needs a due date", 2) }
            var end: EKRecurrenceEnd? = nil
            if let n = rr["count"] as? Int { end = EKRecurrenceEnd(occurrenceCount: n) }
            if let u = rr["until"] as? String { end = EKRecurrenceEnd(end: parseDate(u)) }
            r.addRecurrenceRule(EKRecurrenceRule(recurrenceWith: freq, interval: (rr["interval"] as? Int) ?? 1, end: end))
        }
    }
    // Setting isCompleted stamps completionDate now; an explicit completionDate overrides it.
    if let c = spec["completed"] as? Bool, c != r.isCompleted { r.isCompleted = c }
    if let s = spec["completionDate"] as? String, r.isCompleted { r.completionDate = parseDate(s) }
    return r
}

func save() {
    let input = FileHandle.standardInput.readDataToEndOfFile()
    guard let parsed = try? JSONSerialization.jsonObject(with: input) else { fail("save needs a JSON spec on stdin", 2) }
    let specs: [[String: Any]]
    if let one = parsed as? [String: Any] { specs = [one] } else if let many = parsed as? [[String: Any]] { specs = many } else {
        fail("spec must be an object or an array of objects", 2)
    }
    var saved: [EKReminder] = []
    for spec in specs {
        let r = apply(spec)
        do { try store.save(r, commit: false) } catch { fail("save failed for \(r.title ?? "?"): \(error.localizedDescription)") }
        saved.append(r)
    }
    do { try store.commit() } catch { fail("commit failed: \(error.localizedDescription)") }
    // Read back from a fresh store so the output reflects what was persisted.
    let fresh = EKEventStore()
    let out: [[String: Any]] = saved.map { r in
        if let back = fresh.calendarItem(withIdentifier: r.calendarItemIdentifier) as? EKReminder { return reminderDict(back) }
        return ["id": r.calendarItemIdentifier, "missing": true]
    }
    emit(parsed is [String: Any] ? out[0] : out)
}

// ---- main ---------------------------------------------------------------------

let args = Array(CommandLine.arguments.dropFirst())
guard let cmd = args.first else { fail("usage: ek status|lists|query|get|save|delete|newlist", 2) }
if cmd == "status" {
    emit(["status": authStatus()])
    exit(0)
}
requireAccess()

switch cmd {
case "lists":
    emit(reminderLists().map(listDict))
case "query":
    guard args.count >= 2 else { fail("usage: ek query open|all|completed ...", 2) }
    let kind = args[1]
    var rest = Array(args.dropFirst(2))
    let p: NSPredicate
    switch kind {
    case "open":
        p = store.predicateForIncompleteReminders(withDueDateStarting: nil, ending: nil, calendars: listsById(rest))
    case "all":
        p = store.predicateForReminders(in: listsById(rest))
    case "completed":
        guard rest.count >= 2 else { fail("usage: ek query completed FROM|- TO|- [LIST_ID ...]", 2) }
        let from = rest[0] == "-" ? nil : parseDate(rest[0])
        let to = rest[1] == "-" ? nil : parseDate(rest[1])
        rest = Array(rest.dropFirst(2))
        p = store.predicateForCompletedReminders(withCompletionDateStarting: from, ending: to, calendars: listsById(rest))
    default:
        fail("unknown query \(kind)", 2)
    }
    emit(fetch(p).map(reminderDict))
case "get":
    emit(args.dropFirst().compactMap { id -> [String: Any]? in
        let bare = id.replacingOccurrences(of: "x-apple-reminder://", with: "")
        return (store.calendarItem(withIdentifier: bare) as? EKReminder).map(reminderDict)
    })
case "save":
    save()
case "delete":
    let rs = args.dropFirst().map(reminder)
    for r in rs {
        do { try store.remove(r, commit: false) } catch { fail("delete failed for \(r.title ?? "?"): \(error.localizedDescription)") }
    }
    do { try store.commit() } catch { fail("commit failed: \(error.localizedDescription)") }
    emit(["deleted": rs.map { $0.calendarItemIdentifier }])
case "newlist":
    guard args.count >= 2 else { fail("usage: ek newlist TITLE [SOURCE_TITLE]", 2) }
    let c = EKCalendar(for: .reminder, eventStore: store)
    c.title = args[1]
    if args.count >= 3 {
        guard let src = reminderLists().compactMap({ $0.source }).first(where: { $0.title == args[2] }) else {
            fail("no account named \(args[2]) that holds reminder lists", 2)
        }
        c.source = src
    } else {
        guard let src = store.defaultCalendarForNewReminders()?.source else { fail("no default reminder account", 2) }
        c.source = src
    }
    do { try store.saveCalendar(c, commit: true) } catch { fail("creating the list failed: \(error.localizedDescription)") }
    emit(listDict(c))
default:
    fail("unknown command \(cmd)", 2)
}
