# Encoding policy

All project text files use UTF-8 without a byte-order mark and LF line endings.
This applies to Python, Markdown, YAML, and requirements files.

Each bundled Python CLI configures stdin, stdout, and stderr as UTF-8 at startup,
so JSON containing Chinese or other Unicode text does not depend on the Windows
console code page. Input piped to commands such as `webuse mem record --stdin`
must likewise be UTF-8. PowerShell 7 uses UTF-8 for native pipes; when using
legacy Windows PowerShell, pass UTF-8 bytes through a subprocess or a UTF-8 file.

`.editorconfig` defines the editor behavior and `.gitattributes` preserves LF
line endings if this directory is later placed under Git.
