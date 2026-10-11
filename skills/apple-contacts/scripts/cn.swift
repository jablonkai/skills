// Contacts-framework helper for the apple-contacts skill: one command per run, JSON out.
//
//   cn status                         authorization state, no prompt
//   cn containers                     accounts (iCloud, Exchange, On My Mac …) with counts
//   cn groups                         every group with its container and member count
//   cn contacts [--group ID] [--container ID] [--ids ID,ID] [--raw]
//                                     contacts as JSON (unified across linked cards unless --raw)
//   cn vcard [same filters]           vCard 3.0 text of those contacts on stdout
//   cn parse-vcard FILE               a .vcf file as contact JSON (nothing is saved)
//   cn save < spec.json               ordered create/update/group/member/delete operations
//
// Notes are not available here: the framework drops CNContactNoteKey without an Apple
// entitlement, so the Python side reads and writes notes through JXA.
// Exit codes: 0 ok, 2 bad input or not found, 3 no contacts access, 1 framework error.
import Contacts
import Foundation

let store = CNContactStore()

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

let statusNames: [CNAuthorizationStatus: String] = [
    .notDetermined: "notDetermined", .restricted: "restricted", .denied: "denied", .authorized: "authorized",
]

func authStatus() -> String {
    let st = CNContactStore.authorizationStatus(for: .contacts)
    return statusNames[st] ?? (st.rawValue == 4 ? "limited" : "unknown")
}

// Ask once when undecided; afterwards only System Settings can change the answer.
func requireAccess() {
    if CNContactStore.authorizationStatus(for: .contacts) == .notDetermined {
        let sem = DispatchSemaphore(value: 0)
        store.requestAccess(for: .contacts) { _, _ in sem.signal() }
        sem.wait()
    }
    let st = authStatus()
    if st == "authorized" || st == "limited" { return }
    fail("no access to Contacts (\(st)): enable this terminal/IDE in System Settings > "
        + "Privacy & Security > Contacts", 3)
}

// ---- labels -------------------------------------------------------------------

let labelIn: [String: String] = [
    "home": CNLabelHome, "work": CNLabelWork, "other": CNLabelOther, "school": CNLabelSchool,
    "mobile": CNLabelPhoneNumberMobile, "cell": CNLabelPhoneNumberMobile, "iphone": CNLabelPhoneNumberiPhone,
    "main": CNLabelPhoneNumberMain, "homefax": CNLabelPhoneNumberHomeFax, "workfax": CNLabelPhoneNumberWorkFax,
    "pager": CNLabelPhoneNumberPager, "homepage": CNLabelURLAddressHomePage,
]

func shortLabel(_ raw: String?) -> String {
    guard let raw = raw, !raw.isEmpty else { return "" }
    if raw.hasPrefix("_$!<") && raw.hasSuffix(">!$_") {
        return String(raw.dropFirst(4).dropLast(4)).lowercased()
    }
    return raw
}

func cnLabel(_ s: String?) -> String? {
    guard let s = s, !s.isEmpty else { return nil }
    return labelIn[s.lowercased()] ?? s
}

// ---- contact <-> JSON -----------------------------------------------------------

var keys: [CNKeyDescriptor] = [
    CNContactIdentifierKey, CNContactTypeKey, CNContactNamePrefixKey, CNContactGivenNameKey,
    CNContactMiddleNameKey, CNContactFamilyNameKey, CNContactNameSuffixKey, CNContactNicknameKey,
    CNContactOrganizationNameKey, CNContactDepartmentNameKey, CNContactJobTitleKey,
    CNContactEmailAddressesKey, CNContactPhoneNumbersKey, CNContactPostalAddressesKey,
    CNContactUrlAddressesKey, CNContactBirthdayKey,
].map { $0 as CNKeyDescriptor }

func birthdayString(_ d: DateComponents?) -> String {
    guard let d = d, let m = d.month, let day = d.day else { return "" }
    if let y = d.year, y != NSDateComponentUndefined { return String(format: "%04d-%02d-%02d", y, m, day) }
    return String(format: "--%02d-%02d", m, day)
}

func parseBirthday(_ s: String) -> DateComponents? {
    let parts = s.split(separator: "-", omittingEmptySubsequences: true).compactMap { Int($0) }
    var dc = DateComponents()
    if s.hasPrefix("--"), parts.count == 2 {
        dc.month = parts[0]; dc.day = parts[1]
    } else if parts.count == 3 {
        dc.year = parts[0]; dc.month = parts[1]; dc.day = parts[2]
    } else {
        return nil
    }
    return dc
}

func toJSON(_ c: CNContact, containers: [String: [String]], groups: [String: [String]]) -> [String: Any] {
    var o: [String: Any] = [
        "id": c.identifier,
        "type": c.contactType == .organization ? "organization" : "person",
        "prefix": c.namePrefix, "given": c.givenName, "middle": c.middleName, "family": c.familyName,
        "suffix": c.nameSuffix, "nickname": c.nickname, "org": c.organizationName,
        "department": c.departmentName, "jobTitle": c.jobTitle,
        "birthday": birthdayString(c.birthday),
        "containers": containers[c.identifier] ?? [], "groups": groups[c.identifier] ?? [],
    ]
    o["emails"] = c.emailAddresses.map { ["label": shortLabel($0.label), "value": $0.value as String] }
    o["phones"] = c.phoneNumbers.map { ["label": shortLabel($0.label), "value": $0.value.stringValue] }
    o["urls"] = c.urlAddresses.map { ["label": shortLabel($0.label), "value": $0.value as String] }
    o["addresses"] = c.postalAddresses.map { lv -> [String: String] in
        let a = lv.value
        return ["label": shortLabel(lv.label), "street": a.street, "city": a.city, "state": a.state,
                "postalCode": a.postalCode, "country": a.country, "countryCode": a.isoCountryCode]
    }
    return o
}

func str(_ d: [String: Any], _ k: String) -> String? { d[k] as? String }

func list(_ d: [String: Any], _ k: String) -> [[String: Any]]? { d[k] as? [[String: Any]] }

func phoneDigits(_ s: String) -> String { s.filter { $0.isNumber } }

// Apply a JSON contact to a mutable one. merge: lists gain missing values, empty scalars
// are left alone. replace: given lists replace the stored ones.
func apply(_ d: [String: Any], to c: CNMutableContact, merge: Bool) {
    let scalars: [(String, ReferenceWritableKeyPath<CNMutableContact, String>)] = [
        ("prefix", \.namePrefix), ("given", \.givenName), ("middle", \.middleName), ("family", \.familyName),
        ("suffix", \.nameSuffix), ("nickname", \.nickname), ("org", \.organizationName),
        ("department", \.departmentName), ("jobTitle", \.jobTitle),
    ]
    for (k, path) in scalars {
        if let v = str(d, k), !(merge && v.isEmpty) { c[keyPath: path] = v }
    }
    if let t = str(d, "type") { c.contactType = t == "organization" ? .organization : .person }
    if let b = str(d, "birthday"), !b.isEmpty {
        guard let dc = parseBirthday(b) else { fail("bad birthday \(b) (want YYYY-MM-DD or --MM-DD)", 2) }
        c.birthday = dc
    }
    if let emails = list(d, "emails") {
        let new = emails.compactMap { e -> CNLabeledValue<NSString>? in
            guard let v = str(e, "value"), !v.isEmpty else { return nil }
            return CNLabeledValue(label: cnLabel(str(e, "label")), value: v as NSString)
        }
        if merge {
            let have = Set(c.emailAddresses.map { ($0.value as String).lowercased() })
            c.emailAddresses += new.filter { !have.contains(($0.value as String).lowercased()) }
        } else {
            c.emailAddresses = new
        }
    }
    if let phones = list(d, "phones") {
        let new = phones.compactMap { p -> CNLabeledValue<CNPhoneNumber>? in
            guard let v = str(p, "value"), !v.isEmpty else { return nil }
            return CNLabeledValue(label: cnLabel(str(p, "label")), value: CNPhoneNumber(stringValue: v))
        }
        if merge {
            let have = Set(c.phoneNumbers.map { phoneDigits($0.value.stringValue) })
            c.phoneNumbers += new.filter { !have.contains(phoneDigits($0.value.stringValue)) }
        } else {
            c.phoneNumbers = new
        }
    }
    if let urls = list(d, "urls") {
        let new = urls.compactMap { u -> CNLabeledValue<NSString>? in
            guard let v = str(u, "value"), !v.isEmpty else { return nil }
            return CNLabeledValue(label: cnLabel(str(u, "label")), value: v as NSString)
        }
        if merge {
            let have = Set(c.urlAddresses.map { $0.value as String })
            c.urlAddresses += new.filter { !have.contains($0.value as String) }
        } else {
            c.urlAddresses = new
        }
    }
    if let addrs = list(d, "addresses") {
        let new = addrs.map { a -> CNLabeledValue<CNPostalAddress> in
            let p = CNMutablePostalAddress()
            p.street = str(a, "street") ?? ""; p.city = str(a, "city") ?? ""; p.state = str(a, "state") ?? ""
            p.postalCode = str(a, "postalCode") ?? ""; p.country = str(a, "country") ?? ""
            p.isoCountryCode = (str(a, "countryCode") ?? "").lowercased()
            return CNLabeledValue(label: cnLabel(str(a, "label")), value: p)
        }
        if merge {
            let have = Set(c.postalAddresses.map { "\($0.value.street)|\($0.value.city)".lowercased() })
            c.postalAddresses += new.filter { !have.contains("\($0.value.street)|\($0.value.city)".lowercased()) }
        } else {
            c.postalAddresses = new
        }
    }
}

// ---- lookups --------------------------------------------------------------------

func containerMap() -> [String: [String]] {
    var out: [String: [String]] = [:]
    for ct in (try? store.containers(matching: nil)) ?? [] {
        let pred = CNContact.predicateForContactsInContainer(withIdentifier: ct.identifier)
        let ids = (try? store.unifiedContacts(matching: pred, keysToFetch: [CNContactIdentifierKey as CNKeyDescriptor])) ?? []
        for c in ids { out[c.identifier, default: []].append(ct.identifier) }
    }
    return out
}

func groupMap() -> [String: [String]] {
    var out: [String: [String]] = [:]
    for g in (try? store.groups(matching: nil)) ?? [] {
        let pred = CNContact.predicateForContactsInGroup(withIdentifier: g.identifier)
        let ids = (try? store.unifiedContacts(matching: pred, keysToFetch: [CNContactIdentifierKey as CNKeyDescriptor])) ?? []
        for c in ids { out[c.identifier, default: []].append(g.identifier) }
    }
    return out
}

func containerOfGroup(_ id: String) -> String {
    let pred = CNContainer.predicateForContainerOfGroup(withIdentifier: id)
    return ((try? store.containers(matching: pred)) ?? []).first?.identifier ?? ""
}

func flag(_ args: [String], _ name: String) -> String? {
    guard let i = args.firstIndex(of: name), i + 1 < args.count else { return nil }
    return args[i + 1]
}

// Contacts selected by --group / --container / --ids (all when none), unified unless --raw.
func select(_ args: [String], keysToFetch: [CNKeyDescriptor]) -> [CNContact] {
    let raw = args.contains("--raw")
    var pred: NSPredicate?
    if let g = flag(args, "--group") {
        pred = CNContact.predicateForContactsInGroup(withIdentifier: g)
    } else if let ct = flag(args, "--container") {
        pred = CNContact.predicateForContactsInContainer(withIdentifier: ct)
    } else if let ids = flag(args, "--ids") {
        pred = CNContact.predicateForContacts(withIdentifiers: ids.split(separator: ",").map(String.init))
    }
    let req = CNContactFetchRequest(keysToFetch: keysToFetch)
    req.predicate = pred
    req.unifyResults = !raw
    req.sortOrder = .familyName
    var out: [CNContact] = []
    do {
        try store.enumerateContacts(with: req) { c, _ in out.append(c) }
    } catch {
        fail("fetching contacts failed: \(error.localizedDescription)")
    }
    return out
}

// ---- commands -------------------------------------------------------------------

func cmdContainers() {
    let def = store.defaultContainerIdentifier()
    let types: [CNContainerType: String] = [.local: "local", .exchange: "exchange", .cardDAV: "cardDAV"]
    var out: [[String: Any]] = []
    for ct in (try? store.containers(matching: nil)) ?? [] {
        let pred = CNContact.predicateForContactsInContainer(withIdentifier: ct.identifier)
        let n = ((try? store.unifiedContacts(matching: pred, keysToFetch: [CNContactIdentifierKey as CNKeyDescriptor])) ?? []).count
        out.append(["id": ct.identifier, "name": ct.name, "type": types[ct.type] ?? "unassigned",
                    "default": ct.identifier == def, "count": n])
    }
    emit(out)
}

func cmdGroups() {
    var out: [[String: Any]] = []
    for g in (try? store.groups(matching: nil)) ?? [] {
        let pred = CNContact.predicateForContactsInGroup(withIdentifier: g.identifier)
        let n = ((try? store.unifiedContacts(matching: pred, keysToFetch: [CNContactIdentifierKey as CNKeyDescriptor])) ?? []).count
        out.append(["id": g.identifier, "name": g.name, "container": containerOfGroup(g.identifier), "count": n])
    }
    emit(out)
}

func cmdContacts(_ args: [String]) {
    let cs = select(args, keysToFetch: keys)
    let cm = containerMap(), gm = groupMap()
    emit(cs.map { toJSON($0, containers: cm, groups: gm) })
}

func cmdVcard(_ args: [String]) {
    let cs = select(args, keysToFetch: [CNContactVCardSerialization.descriptorForRequiredKeys()])
    guard !cs.isEmpty else { return }
    do {
        FileHandle.standardOutput.write(try CNContactVCardSerialization.data(with: cs))
    } catch {
        fail("vCard serialization failed: \(error.localizedDescription)")
    }
}

func cmdParseVcard(_ path: String) {
    guard let data = FileManager.default.contents(atPath: path) else { fail("cannot read \(path)", 2) }
    do {
        let cs = try CNContactVCardSerialization.contacts(with: data)
        emit(cs.map { toJSON($0, containers: [:], groups: [:]) })
    } catch {
        fail("\(path) is not a readable vCard file: \(error.localizedDescription)", 2)
    }
}

func fetchOne(_ id: String) -> CNMutableContact {
    let pred = CNContact.predicateForContacts(withIdentifiers: [id])
    guard let c = (try? store.unifiedContacts(matching: pred, keysToFetch: keys))?.first else {
        fail("no contact with id \(id)", 2)
    }
    return c.mutableCopy() as! CNMutableContact
}

func fetchGroup(_ id: String) -> CNGroup {
    guard let g = (try? store.groups(matching: CNGroup.predicateForGroups(withIdentifiers: [id])))?.first else {
        fail("no group with id \(id)", 2)
    }
    return g
}

// Operations run in order inside one save request; "ref" names a new contact or group
// so later operations in the same spec can point at it before it has an id.
func cmdSave() {
    let input = FileHandle.standardInput.readDataToEndOfFile()
    guard let spec = (try? JSONSerialization.jsonObject(with: input)) as? [String: Any],
          let ops = spec["ops"] as? [[String: Any]] else { fail("save wants {\"ops\": [...]} on stdin", 2) }
    let req = CNSaveRequest()
    var contacts: [String: CNContact] = [:], groups: [String: CNGroup] = [:]
    func contact(_ key: String) -> CNContact { contacts[key] ?? fetchOne(key) }
    func group(_ key: String) -> CNGroup { groups[key] ?? fetchGroup(key) }
    for op in ops {
        let ref = str(op, "ref")
        switch str(op, "op") ?? "" {
        case "createGroup":
            guard let name = str(op, "name"), let ct = str(op, "container") else { fail("createGroup needs name and container", 2) }
            let g = CNMutableGroup(); g.name = name
            req.add(g, toContainerWithIdentifier: ct)
            groups[ref ?? name] = g
        case "create":
            guard let d = op["contact"] as? [String: Any], let ct = str(op, "container") else { fail("create needs contact and container", 2) }
            let c = CNMutableContact()
            apply(d, to: c, merge: false)
            req.add(c, toContainerWithIdentifier: ct)
            if let ref = ref { contacts[ref] = c }
        case "update":
            guard let id = str(op, "id"), let d = op["contact"] as? [String: Any] else { fail("update needs id and contact", 2) }
            let c = fetchOne(id)
            apply(d, to: c, merge: (str(op, "mode") ?? "merge") == "merge")
            req.update(c)
            contacts[id] = c
        case "addMember", "removeMember":
            guard let ck = str(op, "contact"), let gk = str(op, "group") else { fail("\(op["op"]!) needs contact and group", 2) }
            if str(op, "op") == "addMember" { req.addMember(contact(ck), to: group(gk)) } else { req.removeMember(contact(ck), from: group(gk)) }
        case "delete":
            guard let id = str(op, "id") else { fail("delete needs id", 2) }
            req.delete(fetchOne(id))
        case "deleteGroup":
            guard let id = str(op, "id") else { fail("deleteGroup needs id", 2) }
            // Deleting a group that still has members fails in CoreData (Cocoa error 134092),
            // so empty it first; the member contacts themselves are kept.
            let g = fetchGroup(id)
            let pred = CNContact.predicateForContactsInGroup(withIdentifier: id)
            for m in (try? store.unifiedContacts(matching: pred, keysToFetch: [CNContactIdentifierKey as CNKeyDescriptor])) ?? [] {
                req.removeMember(m, from: g)
            }
            req.delete(g.mutableCopy() as! CNMutableGroup)
        default:
            fail("unknown op \(op["op"] ?? "nil")", 2)
        }
    }
    do {
        try store.execute(req)
    } catch {
        fail("saving failed: \(error.localizedDescription) \((error as NSError).userInfo)")
    }
    var refs: [String: String] = [:]
    for (k, c) in contacts { refs[k] = c.identifier }
    for (k, g) in groups { refs[k] = g.identifier }
    emit(["ok": true, "refs": refs])
}

let args = Array(CommandLine.arguments.dropFirst())
guard let cmd = args.first else { fail("usage: cn status|containers|groups|contacts|vcard|parse-vcard|save", 2) }
let rest = Array(args.dropFirst())
if cmd == "status" { emit(["status": authStatus()]); exit(0) }
if cmd == "parse-vcard" {
    guard let path = rest.first else { fail("parse-vcard needs a file", 2) }
    cmdParseVcard(path); exit(0)
}
requireAccess()
switch cmd {
case "containers": cmdContainers()
case "groups": cmdGroups()
case "contacts": cmdContacts(rest)
case "vcard": cmdVcard(rest)
case "save": cmdSave()
default: fail("unknown command \(cmd)", 2)
}
