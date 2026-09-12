# Encoding policy - macOS

Use UTF-8 without BOM and LF for all shipped text. Every bundled CLI configures its
text streams as UTF-8. The unified launcher should be called by absolute path.
The component stdin flags read UTF-8. Send exact UTF-8 bytes for non-sensitive text.
Use native shell quoting or UTF-8 files; never place secrets in either.
