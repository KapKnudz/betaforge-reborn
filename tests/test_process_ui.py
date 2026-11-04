"""Check the buildless process view bootstrap and native disclosure structure."""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import unittest


class ProcessMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.stages = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "details" and attrs.get("id", "").startswith("process-stage-"):
            self.stages.append(attrs)
        if tag == "a":
            self.links.append(attrs["href"])


class ProcessUITests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is required for the buildless UI check")
    def test_bootstrap_and_native_disclosures(self):
        script = r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync("web/progress/process.js", "utf8");
function context(readyState, present) {
  const host = { dataset: {}, classList: { add: name => assert.equal(name, "process-view") }, innerHTML: "" };
  let callback;
  const document = {
    readyState,
    getElementById: id => { assert.equal(id, "process-view"); return present ? host : null; },
    addEventListener: (name, handler, options) => {
      assert.equal(name, "DOMContentLoaded"); assert.equal(options.once, true); callback = handler;
    }
  };
  const sandbox = vm.createContext({ document });
  vm.runInContext(source, sandbox);
  return { host, sandbox, fire: () => callback() };
}
const immediate = context("interactive", true);
assert(immediate.host.innerHTML.includes("process-stage-review"));
const markup = immediate.host.innerHTML;
immediate.host.innerHTML = "already rendered";
vm.runInContext(source, immediate.sandbox);
assert.equal(immediate.host.innerHTML, "already rendered");
const deferred = context("loading", true);
assert.equal(deferred.host.innerHTML, "");
deferred.fire();
assert.equal(deferred.host.innerHTML, markup);
assert.equal(context("complete", false).host.innerHTML, "");
assert(!markup.includes("<script"));
assert(!markup.includes("<iframe"));
process.stdout.write(markup);
'''
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(["node", "-e", script], cwd=root, check=True, capture_output=True, text=True)
        markup = ProcessMarkup()
        markup.feed(result.stdout)
        self.assertEqual(len(markup.ids), len(set(markup.ids)))
        self.assertEqual(len(markup.stages), 6)
        self.assertTrue(all("open" not in stage for stage in markup.stages))
        for href in markup.links:
            self.assertTrue(href.startswith("/docs/"))
            self.assertTrue((root / href.removeprefix("/docs/")).is_file(), href)


if __name__ == "__main__":
    unittest.main()
