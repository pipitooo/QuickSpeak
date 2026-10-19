# Security and privacy

This project is in early development. Only the current `main` branch is maintained.

QuickSpeak handles text selected in other applications. Avoid posting a private
passage, clipboard dump, token, personal file or screenshot in a public issue.
Reproduce problems with synthetic text whenever possible.

For a vulnerability that could expose text, execute unintended commands or affect
another application, use GitHub's private vulnerability reporting if that option
is available on this repository. Otherwise open a minimal issue asking for a
private contact channel, without exploit details or sensitive information.

The application does not accept remote commands or host a network service. Setup
downloads Python packages and model files. The model revision and hashes are pinned;
downloaded Python dependencies execute code during installation/runtime. Install
from this repository and the linked upstream sources only.

Windows clipboard managers/history can observe clipboard fallback copies. This is
an OS/application boundary, not a claim that clipboard restoration erases history.
