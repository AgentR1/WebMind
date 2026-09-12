# Encoding policy - Windows

Use UTF-8 without BOM and LF for all shipped text. Every bundled CLI configures its
text streams as UTF-8. The unified launcher should be called by absolute path.
Use the Codex launcher `--input-file` for complex non-sensitive UTF-8 input.
Legacy PowerShell native pipes may transform encoding; do not infer exact byte preservation.
