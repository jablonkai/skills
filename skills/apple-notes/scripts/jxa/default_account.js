// default_account.js {} -> "iCloud"
function run(argv) {
  return JSON.stringify(Application("Notes").defaultAccount().name());
}
