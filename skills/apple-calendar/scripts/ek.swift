// EventKit helper for the apple-calendar skill: one command per run, JSON out on stdout.
//
//   ek status                                  authorization state, no prompt
//   ek calendars                               every event calendar
//   ek range FROM TO [CAL_ID ...]              occurrences in [FROM, TO), recurrences expanded
//   ek get ID [OCCURRENCE]                     one event (series start, or one occurrence)
//   ek save < spec.json                        create or update, then read back
//   ek delete ID [OCCURRENCE] this|future      remove one occurrence or the rest of a series
//
// Dates are ISO 8601 with an offset (2026-10-20T10:00:00+02:00) or a bare date
// (2026-10-20, local midnight). Output dates carry the local offset.
// Exit codes: 0 ok, 2 bad input or not found, 3 no calendar access, 1 EventKit error.
import EventKit
import Foundation

let store = EKEventStore()
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

func authStatus() -> String { statusNames[EKEventStore.authorizationStatus(for: .event)] ?? "unknown" }

// Ask once when undecided; afterwards only System Settings can change the answer.
func requireAccess(write: Bool) {
    var st = EKEventStore.authorizationStatus(for: .event)
    if st == .notDetermined {
        let sem = DispatchSemaphore(value: 0)
        store.requestFullAccessToEvents { _, _ in sem.signal() }
        sem.wait()
        st = EKEventStore.authorizationStatus(for: .event)
    }
    if st == .fullAccess || (write && st == .writeOnly) { return }
    fail("calendar access is \(statusNames[st] ?? "unknown"): turn on Full Access for this terminal/IDE in "
        + "System Settings > Privacy & Security > Calendars, then retry", 3)
}

// ---- encoding ----------------------------------------------------------------

let freqNames: [EKRecurrenceFrequency: String] = [.daily: "DAILY", .weekly: "WEEKLY", .monthly: "MONTHLY", .yearly: "YEARLY"]
let dayNames: [EKWeekday: String] = [.sunday: "SU", .monday: "MO", .tuesday: "TU", .wednesday: "WE",
                                     .thursday: "TH", .friday: "FR", .saturday: "SA"]

func ruleString(_ r: EKRecurrenceRule) -> String {
    var parts = ["FREQ=\(freqNames[r.frequency] ?? "DAILY")"]
    if r.interval > 1 { parts.append("INTERVAL=\(r.interval)") }
    if let days = r.daysOfTheWeek, !days.isEmpty {
        parts.append("BYDAY=" + days.map { ($0.weekNumber != 0 ? "\($0.weekNumber)" : "") + (dayNames[$0.dayOfTheWeek] ?? "") }.joined(separator: ","))
    }
    if let v = r.daysOfTheMonth, !v.isEmpty { parts.append("BYMONTHDAY=" + v.map { "\($0)" }.joined(separator: ",")) }
    if let v = r.monthsOfTheYear, !v.isEmpty { parts.append("BYMONTH=" + v.map { "\($0)" }.joined(separator: ",")) }
    if let v = r.setPositions, !v.isEmpty { parts.append("BYSETPOS=" + v.map { "\($0)" }.joined(separator: ",")) }
    if let end = r.recurrenceEnd {
        if end.occurrenceCount > 0 {
            parts.append("COUNT=\(end.occurrenceCount)")
        } else if let d = end.endDate {
            let f = DateFormatter()
            f.locale = Locale(identifier: "en_US_POSIX")
            f.timeZone = TimeZone(identifier: "UTC")
            f.dateFormat = "yyyyMMdd'T'HHmmss'Z'"
            parts.append("UNTIL=" + f.string(from: d))
        }
    }
    return parts.joined(separator: ";")
}

func alarmDict(_ a: EKAlarm) -> [String: Any] {
    if let d = a.absoluteDate { return ["absolute": iso.string(from: d)] }
    return ["offsetMinutes": Int((a.relativeOffset / 60).rounded())]
}

let participantStatus: [EKParticipantStatus: String] = [
    .unknown: "unknown", .pending: "pending", .accepted: "accepted", .declined: "declined",
    .tentative: "tentative", .delegated: "delegated", .completed: "completed", .inProcess: "inProcess",
]
let availabilityNames: [EKEventAvailability: String] = [
    .notSupported: "notSupported", .busy: "busy", .free: "free", .tentative: "tentative", .unavailable: "unavailable",
]

func eventDict(_ e: EKEvent) -> [String: Any] {
    var d: [String: Any] = [
        "id": e.eventIdentifier ?? "",
        "externalId": e.calendarItemExternalIdentifier ?? "",
        "title": e.title ?? "",
        "start": iso.string(from: e.startDate),
        "end": iso.string(from: e.endDate),
        "allDay": e.isAllDay,
        "calendar": e.calendar.title,
        "calendarId": e.calendar.calendarIdentifier,
        "source": e.calendar.source.title,
        "recurring": e.hasRecurrenceRules,
        "detached": e.isDetached,
        "availability": availabilityNames[e.availability] ?? "busy",
        "alarms": (e.alarms ?? []).sorted { ($0.absoluteDate == nil ? 0 : 1, $0.relativeOffset) < ($1.absoluteDate == nil ? 0 : 1, $1.relativeOffset) }
            .map(alarmDict),
    ]
    if e.isAllDay {
        d["startDate"] = dayFmt.string(from: e.startDate)
        d["endDate"] = dayFmt.string(from: e.endDate)
    }
    if let o = e.occurrenceDate { d["occurrence"] = iso.string(from: o) }
    if let v = e.location, !v.isEmpty { d["location"] = v }
    if let v = e.notes, !v.isEmpty { d["notes"] = v }
    if let v = e.url { d["url"] = v.absoluteString }
    if let tz = e.timeZone { d["timeZone"] = tz.identifier }
    if let rules = e.recurrenceRules, !rules.isEmpty { d["rrule"] = rules.map(ruleString) }
    if let ps = e.attendees, !ps.isEmpty {
        d["attendees"] = ps.map { p -> [String: Any] in
            var a: [String: Any] = ["status": participantStatus[p.participantStatus] ?? "unknown",
                                    "self": p.isCurrentUser]
            if let n = p.name { a["name"] = n }
            let url = p.url.absoluteString
            if url.lowercased().hasPrefix("mailto:") { a["email"] = String(url.dropFirst(7)) }
            return a
        }
    }
    if e.hasRecurrenceRules, let id = e.eventIdentifier, let first = store.event(withIdentifier: id) {
        d["seriesStart"] = iso.string(from: first.startDate)
        d["seriesEnd"] = iso.string(from: first.endDate)
    }
    return d
}

func calendarDict(_ c: EKCalendar) -> [String: Any] {
    let types: [EKCalendarType: String] = [.local: "local", .calDAV: "calDAV", .exchange: "exchange",
                                           .subscription: "subscription", .birthday: "birthday"]
    return ["id": c.calendarIdentifier, "title": c.title, "source": c.source.title,
            "type": types[c.type] ?? "unknown", "writable": c.allowsContentModifications,
            "default": c.calendarIdentifier == store.defaultCalendarForNewEvents?.calendarIdentifier]
}

// ---- lookup ------------------------------------------------------------------

func calendars(_ ids: [String]) -> [EKCalendar]? {
    if ids.isEmpty { return nil }
    let all = store.calendars(for: .event)
    return ids.map { id -> EKCalendar in
        guard let c = all.first(where: { $0.calendarIdentifier == id }) else { fail("no calendar with id \(id)", 2) }
        return c
    }
}

// An occurrence is (event id, original start). Detached occurrences keep their
// original occurrenceDate, so match on that rather than on the current start.
func findEvent(_ id: String, _ occurrence: String?) -> EKEvent {
    guard let first = store.event(withIdentifier: id) else { fail("no event with id \(id)", 2) }
    guard let occ = occurrence else { return first }
    let at = parseDate(occ)
    let pred = store.predicateForEvents(withStart: at.addingTimeInterval(-2 * 86400),
                                        end: at.addingTimeInterval(2 * 86400), calendars: [first.calendar])
    let hit = store.events(matching: pred).first { e in
        e.eventIdentifier == id && abs((e.occurrenceDate ?? e.startDate).timeIntervalSince(at)) < 1
    }
    guard let found = hit else { fail("event \(id) has no occurrence at \(occ)", 2) }
    return found
}

// ---- writes ------------------------------------------------------------------

let freqByName: [String: EKRecurrenceFrequency] = ["DAILY": .daily, "WEEKLY": .weekly, "MONTHLY": .monthly, "YEARLY": .yearly]
let dayByName: [String: EKWeekday] = ["SU": .sunday, "MO": .monday, "TU": .tuesday, "WE": .wednesday,
                                      "TH": .thursday, "FR": .friday, "SA": .saturday]

// RRULE subset: FREQ, INTERVAL, BYDAY (optionally with a week number, e.g. 2TU / -1FR),
// BYMONTHDAY, BYMONTH, BYSETPOS, COUNT, UNTIL.
func parseRule(_ s: String) -> EKRecurrenceRule {
    var kv: [String: String] = [:]
    for part in s.replacingOccurrences(of: "RRULE:", with: "").split(separator: ";") {
        let p = part.split(separator: "=", maxSplits: 1).map(String.init)
        if p.count == 2 { kv[p[0].uppercased()] = p[1].uppercased() }
    }
    guard let freq = freqByName[kv["FREQ"] ?? ""] else { fail("RRULE needs FREQ=DAILY|WEEKLY|MONTHLY|YEARLY: \(s)", 2) }
    let ints = { (k: String) -> [NSNumber]? in kv[k].map { $0.split(separator: ",").compactMap { Int($0) }.map { NSNumber(value: $0) } } }
    let days: [EKRecurrenceDayOfWeek]? = kv["BYDAY"].map { list in
        list.split(separator: ",").map { tok -> EKRecurrenceDayOfWeek in
            let t = String(tok)
            guard let wd = dayByName[String(t.suffix(2))] else { fail("bad BYDAY \(t)", 2) }
            let n = Int(t.dropLast(2)) ?? 0
            return n == 0 ? EKRecurrenceDayOfWeek(wd) : EKRecurrenceDayOfWeek(wd, weekNumber: n)
        }
    }
    var end: EKRecurrenceEnd?
    if let c = kv["COUNT"], let n = Int(c) {
        end = EKRecurrenceEnd(occurrenceCount: n)
    } else if let u = kv["UNTIL"] {
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_US_POSIX")
        var d: Date?
        for (fmt, tz) in [("yyyyMMdd'T'HHmmss'Z'", "UTC"), ("yyyyMMdd'T'HHmmss", nil), ("yyyyMMdd", nil)] as [(String, String?)] {
            f.dateFormat = fmt
            f.timeZone = tz.flatMap { TimeZone(identifier: $0) } ?? TimeZone.current
            if let x = f.date(from: u) { d = x; break }
        }
        guard var until = d else { fail("bad UNTIL \(u)", 2) }
        if u.count == 8 { until = until.addingTimeInterval(86399) }  // a bare date includes that whole day
        end = EKRecurrenceEnd(end: until)
    }
    return EKRecurrenceRule(recurrenceWith: freq, interval: Int(kv["INTERVAL"] ?? "1") ?? 1,
                            daysOfTheWeek: days, daysOfTheMonth: ints("BYMONTHDAY"), monthsOfTheYear: ints("BYMONTH"),
                            weeksOfTheYear: nil, daysOfTheYear: nil, setPositions: ints("BYSETPOS"), end: end)
}

func save(_ spec: [String: Any]) {
    let event: EKEvent
    let isNew = spec["id"] == nil
    if let id = spec["id"] as? String {
        event = findEvent(id, spec["occurrence"] as? String)
    } else {
        event = EKEvent(eventStore: store)
        let cal: EKCalendar
        if let cid = spec["calendarId"] as? String {
            cal = calendars([cid])![0]
        } else if let def = store.defaultCalendarForNewEvents {
            cal = def
        } else {
            fail("no default calendar; pass calendarId", 2)
        }
        event.calendar = cal
    }
    if !isNew, let cid = spec["calendarId"] as? String, cid != event.calendar.calendarIdentifier {
        event.calendar = calendars([cid])![0]
    }
    if !event.calendar.allowsContentModifications {
        fail("calendar \(event.calendar.title) is read-only (subscribed, holidays or birthdays)", 2)
    }
    if let v = spec["title"] as? String { event.title = v }
    if let v = spec["allDay"] as? Bool { event.isAllDay = v }
    if let tz = spec["timeZone"] as? String {
        guard let z = TimeZone(identifier: tz) else { fail("unknown time zone \(tz)", 2) }
        event.timeZone = z
    }
    if let v = spec["start"] as? String { event.startDate = parseDate(v) }
    if let v = spec["end"] as? String { event.endDate = parseDate(v) }
    if isNew && event.endDate == nil { event.endDate = event.startDate.addingTimeInterval(event.isAllDay ? 0 : 3600) }
    if event.endDate < event.startDate { fail("end is before start", 2) }
    if let v = spec["location"] as? String { event.location = v.isEmpty ? nil : v }
    if let v = spec["notes"] as? String { event.notes = v.isEmpty ? nil : v }
    if let v = spec["url"] as? String { event.url = v.isEmpty ? nil : URL(string: v) }
    if let v = spec["availability"] as? String {
        guard let a = availabilityNames.first(where: { $0.value == v })?.key else { fail("bad availability \(v)", 2) }
        event.availability = a
    }
    if let alarms = spec["alarms"] as? [Any] {
        event.alarms = alarms.map { a -> EKAlarm in
            if let m = a as? NSNumber { return EKAlarm(relativeOffset: m.doubleValue * 60) }
            if let s = a as? String { return EKAlarm(absoluteDate: parseDate(s)) }
            fail("alarm must be minutes (negative = before) or an ISO date", 2)
        }
    }
    if let r = spec["rrule"] {
        if let s = r as? String, !s.isEmpty {
            event.recurrenceRules = [parseRule(s)]
        } else {
            event.recurrenceRules = nil
        }
    }
    let span: EKSpan = (spec["span"] as? String) == "future" ? .futureEvents : .thisEvent
    do {
        try store.save(event, span: span, commit: true)
    } catch {
        fail("save failed: \(error.localizedDescription)")
    }
    // Read back through a fresh store so the answer reflects what was persisted.
    let fresh = EKEventStore()
    guard let id = event.eventIdentifier, let back = fresh.event(withIdentifier: id) else {
        emit(["saved": true, "readback": NSNull(), "note": "saved, but write-only access cannot read it back"])
        return
    }
    var out = eventDict(back)
    if let occ = event.occurrenceDate, back.hasRecurrenceRules || event.isDetached {
        let pred = fresh.predicateForEvents(withStart: occ.addingTimeInterval(-2 * 86400),
                                            end: occ.addingTimeInterval(2 * 86400), calendars: [back.calendar])
        if let o = fresh.events(matching: pred).first(where: { $0.eventIdentifier == id && $0.startDate == event.startDate }) {
            out = eventDict(o)
        }
    }
    emit(["saved": true, "created": isNew, "span": span == .futureEvents ? "future" : "this", "event": out])
}

// ---- main --------------------------------------------------------------------

var args = Array(CommandLine.arguments.dropFirst())
let cmd = args.isEmpty ? "status" : args.removeFirst()
switch cmd {
case "status":
    emit(["status": authStatus()])
case "calendars":
    requireAccess(write: false)
    emit(store.calendars(for: .event).map(calendarDict))
case "range":
    guard args.count >= 2 else { fail("usage: ek range FROM TO [CAL_ID ...]", 2) }
    requireAccess(write: false)
    let from = parseDate(args[0]), to = parseDate(args[1])
    // predicateForEvents silently clips spans longer than four years.
    if to.timeIntervalSince(from) > 4 * 365 * 86400 { fail("range longer than 4 years; split it", 2) }
    let pred = store.predicateForEvents(withStart: from, end: to, calendars: calendars(Array(args.dropFirst(2))))
    let events = store.events(matching: pred).sorted { ($0.startDate, $0.title ?? "") < ($1.startDate, $1.title ?? "") }
    emit(events.map(eventDict))
case "get":
    guard !args.isEmpty else { fail("usage: ek get ID [OCCURRENCE]", 2) }
    requireAccess(write: false)
    emit(eventDict(findEvent(args[0], args.count > 1 ? args[1] : nil)))
case "save":
    requireAccess(write: true)
    let data = FileHandle.standardInput.readDataToEndOfFile()
    guard let spec = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] else { fail("save wants a JSON object on stdin", 2) }
    save(spec)
case "delete":
    guard args.count >= 1 else { fail("usage: ek delete ID [OCCURRENCE] [this|future]", 2) }
    requireAccess(write: true)
    let occ = args.count > 1 && args[1] != "this" && args[1] != "future" ? args[1] : nil
    let span: EKSpan = args.last == "future" ? .futureEvents : .thisEvent
    let e = findEvent(args[0], occ)
    let before = eventDict(e)
    do {
        try store.remove(e, span: span, commit: true)
    } catch {
        fail("delete failed: \(error.localizedDescription)")
    }
    emit(["deleted": true, "span": span == .futureEvents ? "future" : "this", "event": before])
default:
    fail("unknown command \(cmd)", 2)
}
