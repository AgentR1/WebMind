# Reading and interaction workflows

These examples run from the WebMind directory with Python 3.10+. On Windows, `py -3` may replace `python3`. Replace `TAB_ID` with the intended `type: "page"` ID from `tabs`. Example selectors describe a page structure; inspect your page before using them. If using a non-default endpoint, put the same `--endpoint URL` before every command.

The host agent chooses actions and evaluates the evidence. A CLI response describes a browser operation or extraction, not an independently completed user task.

For a concrete web task, consult relevant prior experience using the [memory guide](../references/memory.md). Check it against the current page, then verify the outcome before proposing a new lesson. Persistent records follow the host's memory permissions. For the full experience/browser/desktop flow, see [full workflow](full-workflow.md).

## Read a webpage

```bash
python3 scripts/webmind.py tabs --json
python3 scripts/webmind.py navigate --target-id TAB_ID --url "https://example.com" --wait-load --timeout 15 --json
python3 scripts/webmind.py read-page --target-id TAB_ID --wait-selector "h1" --max-chars 20000 --max-links 100 --json
```

Check navigation `ok` and `status`, then check `page.url` and `page.title` to confirm the destination. Read `page.text`, `page.headings`, and `page.links`, and inspect `page.extraction` and `page.truncated`. If text is truncated, raise `--max-chars` or read a narrower region before claiming the whole article was read. Links are limited separately by `--max-links`.

If the heuristic picks the wrong region, inspect the DOM and select a unique visible container:

```bash
python3 scripts/webmind.py eval --target-id TAB_ID --expression "Array.from(document.querySelectorAll('article, main, [role=main]')).map(e => ({tag: e.tagName, id: e.id, textStart: e.innerText.slice(0, 200)}))" --json
python3 scripts/webmind.py read-page --target-id TAB_ID --selector "article" --max-chars 30000 --max-links 30 --json
```

Use the `article` example only if it uniquely identifies the content. `eval` is useful for custom fields such as a product price or table cell; `read-page` is the first choice for article-like text. Neither provides OCR or cross-frame/Shadow DOM extraction.

## Read content after login

Launch the dedicated browser, then sign in to the requested site in that browser using the user's authorized workflow. WebMind's profile preserves that session for later use; it does not import the everyday browser's login automatically.

```bash
python3 scripts/webmind.py launch --json
python3 scripts/webmind.py tabs --json
python3 scripts/webmind.py read-page --target-id TAB_ID --json
```

Check that the returned URL and text show the requested content. A login screen, access-denied page, or expired-session message is not evidence that the private content was read. Complete any required login or access step through the authorized browser/desktop workflow, then read the page again. Native UI uses the Screenshot/Mouse/Typing module guides, or suitable host GUI tools. WebMind does not bypass authentication or grant access.

For an already observed, unique content container:

```bash
python3 scripts/webmind.py read-page --target-id TAB_ID --selector "main" --max-links 0 --json
```

`--max-links 0` omits returned links. It does not change the session's permissions or guarantee that the text contains no sensitive information; report only content needed for the user's request.

## Wait for dynamic content

`navigate --wait-load` waits for the relevant document navigation, not every asynchronous request. For a page where DOM inspection shows a content-ready marker:

```bash
python3 scripts/webmind.py read-page --target-id TAB_ID --wait-selector "main[data-state=ready]" --selector "main" --timeout 20 --json
```

`--wait-selector` waits for the selector to exist. If an element already exists while empty, choose a marker that appears only when the needed content arrives, or use `eval` to inspect readiness before reading. If visibility itself matters:

```bash
python3 scripts/webmind.py wait-for-selector --target-id TAB_ID --selector "article" --visible --timeout 20 --json
python3 scripts/webmind.py read-page --target-id TAB_ID --selector "article" --json
```

Visibility here means a nonzero layout box; it does not prove the element is unobstructed or semantically complete. Read the extracted content to confirm the expected result. The extractor takes one snapshot and does not automatically paginate, scroll an infinite feed, or wait for future content updates.

## Verify an interaction outcome

Suppose DOM inspection identified a search form with the following fields. Fill the query and verify its value before submitting:

```bash
python3 scripts/webmind.py fill --target-id TAB_ID --selector "input[name=q]" --text "browser automation" --json
python3 scripts/webmind.py eval --target-id TAB_ID --expression "document.querySelector('input[name=q]').value" --json
python3 scripts/webmind.py click --target-id TAB_ID --selector "button[type=submit]" --json
```

Successful input responses report `status: "dispatched"` and `outcome_verified: false`. The fill's `immediate_value_verified` checks only the immediate value after synchronous handlers. It cannot prove that the application retained the value later or accepted a submitted request.

Wait for an observed result-state marker, then read the actual results:

```bash
python3 scripts/webmind.py read-page --target-id TAB_ID --wait-selector "main[data-state=results]" --selector "main" --timeout 15 --json
```

Confirm that the output corresponds to the submitted query, rather than a stale result list, validation error, or login page. The appropriate success evidence depends on the task: a saved item, a specific result, or a confirmation message. For sends, purchases, deletions, and other consequential actions, preserve the user's authorized scope and check for completion before any retry.

## Recover from failures

| Observed failure | Next step |
| --- | --- |
| Multiple page targets or filter matches | Run `tabs`, identify the intended page, and pass its exact ID. |
| Closed or replaced target | Re-list tabs and confirm the new page identity. |
| `navigate` reports `failed` | Read its error and inspect the current URL before changing the request. |
| `navigate` reports `download` | Treat it as a download, not a loaded page; use the host's available file workflow if relevant. |
| Navigation or selector wait times out | Inspect the current page for delayed content, a bad selector, login, or an error before retrying. |
| Extraction returns irrelevant or incomplete text | Inspect `extraction`/`truncated`, choose a unique visible region, or adjust limits. |
| An input command fails or its effect is uncertain | Read the DOM and any confirmation state before repeating the operation. |

For a timeout, inspect without repeating the previous action:

```bash
python3 scripts/webmind.py eval --target-id TAB_ID --expression "({url: location.href, title: document.title, ready: document.readyState})" --json
python3 scripts/webmind.py read-page --target-id TAB_ID --max-chars 5000 --max-links 10 --json
python3 scripts/webmind.py screenshot --target-id TAB_ID --output recovery.png --json
```

For a connection problem on an alternative endpoint:

```bash
python3 scripts/webmind.py --endpoint http://127.0.0.1:9334 --no-auto-launch self-check --json
python3 scripts/webmind.py --endpoint http://127.0.0.1:9334 tabs --json
```

The second command may launch the dedicated browser if the local endpoint is unavailable. Do not reuse a profile concurrently on different ports; close its browser before changing ports or choose a separate profile. For native permission bubbles, file pickers, and OS dialogs, inspect a desktop screenshot and follow the relevant [screenshot](../references/screenshot.md), [mouse](../references/mouse.md), and [typing](../references/typing.md) guides before acting.

## What the tests establish

The opt-in browser tests use real Chrome with a local HTTP site to check controlled reading and interaction scenarios, including failures. Offline tests exercise behavior without a browser. Run instructions are in the [README](../README.md#tests).

Those tests are distinct from a public-website end-to-end benchmark, which would require a defined set of tasks, site/session conditions, outcome criteria, and recorded results. No general website success rate follows from local fixtures. The examples above are usage patterns, not reported benchmark runs.
