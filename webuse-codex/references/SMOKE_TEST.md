# Native Windows/macOS acceptance checklist

Run only on your own machine, with a blank/non-sensitive desktop and a disposable
page. Do not test screenshots during login or while private data is visible.
This checklist is supplied for verification; its presence is not a claim that it
has already been executed on either desktop OS.

1. Install in a source path containing spaces and non-ASCII characters. Run from
   another working directory using the absolute launcher path. Confirm `/skills`
   shows `webuse-codex` and that Codex can read its SKILL.md and component guides.
2. Run `doctor --json`. Check runtime_ready, browser_available and GUI permission
   fields independently. Confirm the reported profile/Mem paths are the intended
   Codex directories, not a source-edition profile or another user's directory.
3. Run `cdp launch --url https://example.com --json`, then `cdp tabs --json` and
   `cdp eval --target-id TARGET --expression "document.title" --json`. Confirm that
   profile_verified is true. Repeating launch must not spawn another profile.
4. Use a harmless local form or a disposable data URL. Test click, fill with a
   UTF-8 Chinese input file, and read the field value. Never substitute an actual
   credential form. Test `--expression-stdin` / dispatcher `--input-file` with
   quotes and newlines, especially in Windows PowerShell 5.1.
5. Capture a non-sensitive desktop region and open its PNG in Codex. Confirm the
   pointer marker and scale metadata. On Retina and Windows scaling above 100%,
   convert the target's image coordinate and move (not click) the pointer. On a
   second monitor, test a negative desktop origin before clicking anything.
6. In a blank text editor with confirmed focus, test `typing type --text hello`,
   `typing hotkey --keys primary a`, and non-sensitive Unicode clipboard paste.
   Confirm Command on macOS and Ctrl on Windows. Leave the PyAutoGUI failsafe on.
7. In a temporary external Mem folder, initialize, read, record, search and
   guarded-rewrite a test note. Verify that an incorrect SHA-256 is rejected and
   that a repeated installation preserves that folder.
8. Confirm that revoked macOS permission produces an actionable failure. On a
   Windows private sandbox desktop, confirm GUI actions stop instead of clicking
   in a different session. Use a user-approved host command when appropriate;
   do not disable the sandbox globally or ignore an explicit denial.
9. Run `python -B scripts/run_tests.py --browser` locally. Tests use a disposable
   headless browser and local HTML; they do not log into websites. The desktop
   permission/focus checklist is separate from those headless browser tests.

Record OS, Python, browser version, display scaling, Codex surface, shell, approval
mode and observed result. A green unit-test run alone is not a GUI acceptance test.
