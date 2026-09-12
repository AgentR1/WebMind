# Encoding policy - macOS

Use UTF-8 without BOM and LF for all shipped text. Every bundled CLI configures its
text streams as UTF-8. The unified launcher should be called by absolute path.
Use the Codex launcher `--input-file` for complex non-sensitive UTF-8 input.
Use native shell quoting or UTF-8 files; never place secrets in either.
