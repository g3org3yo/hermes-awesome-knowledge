# Third-party notices

This project does not vendor upstream content. `scripts/bootstrap.py` clones the
repositories below as data into `$RAW_ROOT` (gitignored, platform cache directory by default);
each clone keeps its own license file, and the retrieval tools return that content verbatim.

| Repository | Project | License | License file | Installed as |
|---|---|---|---|---|
| `awesome-algorithms` | [Awesome Algorithms](https://github.com/tayllan/awesome-algorithms) | CC-BY-4.0 | `README.md` | `$RAW_ROOT/awesome-algorithms` |
| `awesome-android-ui` | [Awesome Android UI](https://github.com/wasabeef/awesome-android-ui) | MIT | `LICENSE` | `$RAW_ROOT/awesome-android-ui` |
| `awesome-cpp` | [Awesome C++](https://github.com/fffaraz/awesome-cpp) | MIT | `LICENSE` | `$RAW_ROOT/awesome-cpp` |
| `awesome-design-patterns` | [Awesome Design Patterns](https://github.com/DovAmir/awesome-design-patterns) | see upstream | — | `$RAW_ROOT/awesome-design-patterns` |
| `awesome-for-beginners` | [Awesome for Beginners](https://github.com/MunGell/awesome-for-beginners) | see upstream | — | `$RAW_ROOT/awesome-for-beginners` |
| `awesome-go` | [Awesome Go](https://github.com/avelino/awesome-go) | MIT | `LICENSE` | `$RAW_ROOT/awesome-go` |
| `awesome-hacking` | [Awesome Hacking](https://github.com/Hack-with-Github/Awesome-Hacking) | CC (see LICENSE) | `LICENSE` | `$RAW_ROOT/Awesome-Hacking` |
| `awesome-java` | [Awesome Java](https://github.com/akullpp/awesome-java) | CC (see LICENSE) | `LICENSE` | `$RAW_ROOT/awesome-java` |
| `awesome-llm-apps` | [Awesome LLM Apps](https://github.com/Shubhamsaboo/awesome-llm-apps) | Apache-2.0 | `LICENSE` | `$RAW_ROOT/awesome-llm-apps` |
| `awesome-malware-analysis` | [Awesome Malware Analysis](https://github.com/rshipp/awesome-malware-analysis) | CC-BY-4.0 | `LICENSE` | `$RAW_ROOT/awesome-malware-analysis` |
| `awesome-mcp-servers` | [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers) | MIT | `LICENSE` | `$RAW_ROOT/awesome-mcp-servers` |
| `awesome-meta` | [Awesome (sindresorhus)](https://github.com/sindresorhus/awesome) | CC0-1.0 | `license` | `$RAW_ROOT/awesome-meta` |
| `awesome-nodejs` | [Awesome Node.js](https://github.com/sindresorhus/awesome-nodejs) | CC (see LICENSE) | `license` | `$RAW_ROOT/awesome-nodejs` |
| `awesome-public-datasets` | [Awesome Public Datasets](https://github.com/awesomedata/awesome-public-datasets) | MIT | `LICENSE` | `$RAW_ROOT/awesome-public-datasets` |
| `awesome-python` | [Awesome Python](https://github.com/vinta/awesome-python) | CC (see LICENSE) | `LICENSE` | `$RAW_ROOT/awesome-python` |
| `awesome-rust` | [Awesome Rust](https://github.com/rust-unofficial/awesome-rust) | CC (see LICENSE) | `LICENSE.txt` | `$RAW_ROOT/awesome-rust` |
| `awesome-scalability` | [Awesome Scalability](https://github.com/binhnguyennus/awesome-scalability) | MIT | `LICENSE` | `$RAW_ROOT/awesome-scalability` |
| `awesome-selfhosted` | [Awesome Selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted) | CC (see LICENSE) | `LICENSE` | `$RAW_ROOT/awesome-selfhosted` |
| `awesome-software-architecture` | [Awesome Software Architecture](https://github.com/simskij/awesome-software-architecture) | CC0-1.0 | `license.md` | `$RAW_ROOT/awesome-software-architecture` |
| `awesome-threat-intelligence` | [Awesome Threat Intelligence](https://github.com/hslatman/awesome-threat-intelligence) | Apache-2.0 | `LICENSE` | `$RAW_ROOT/awesome-threat-intelligence` |
| `awesome-web-security` | [Awesome Web Security](https://github.com/qazbnm456/awesome-web-security) | CC0-1.0 | `README.md` | `$RAW_ROOT/awesome-web-security` |
| `book-of-secret-knowledge` | [The Book of Secret Knowledge](https://github.com/trimstray/the-book-of-secret-knowledge) | MIT | `LICENSE.md` | `$RAW_ROOT/the-book-of-secret-knowledge` |
| `build-your-own-x` | [Build Your Own X](https://github.com/codecrafters-io/build-your-own-x) | NO LICENSE | — | `$RAW_ROOT/build-your-own-x` |
| `github-cheat-sheet` | [GitHub Cheat Sheet](https://github.com/tiimgreen/github-cheat-sheet) | MIT | `LICENSE` | `$RAW_ROOT/github-cheat-sheet` |

The engine (`bin/awesome.py`), the plugin adapter (`__init__.py`), the provisioning and
update scripts and the tests are original work, licensed MIT (see `LICENSE`).

List content — README text, link descriptions, section headings — remains under the license
of the respective upstream project. If you redistribute a built index (`index.db`), it
contains derived excerpts of that content; keep this file with it.

License families were detected from the first lines of each upstream license file; consult
the upstream repository for the authoritative text.
