# Third-party notices

This project does not vendor upstream content. `scripts/bootstrap.py` clones the
repositories below as data into `data/raw/` (gitignored); each clone keeps its own license
file, and the retrieval tools return that content verbatim.

| Repository | Project | License | License file | Installed as |
|---|---|---|---|---|
| `awesome-selfhosted` | [Awesome Selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted) | CC (see LICENSE) | `LICENSE` | `data/raw/awesome-selfhosted` |
| `awesome-python` | [Awesome Python](https://github.com/vinta/awesome-python) | CC (see LICENSE) | `LICENSE` | `data/raw/awesome-python` |
| `book-of-secret-knowledge` | [The Book of Secret Knowledge](https://github.com/trimstray/the-book-of-secret-knowledge) | MIT | `LICENSE.md` | `data/raw/the-book-of-secret-knowledge` |
| `awesome-go` | [Awesome Go](https://github.com/avelino/awesome-go) | MIT | `LICENSE` | `data/raw/awesome-go` |
| `awesome-hacking` | [Awesome Hacking](https://github.com/Hack-with-Github/Awesome-Hacking) | CC (see LICENSE) | `LICENSE` | `data/raw/Awesome-Hacking` |
| `awesome-for-beginners` | [Awesome for Beginners](https://github.com/MunGell/awesome-for-beginners) | see upstream | — | `data/raw/awesome-for-beginners` |
| `awesome-scalability` | [Awesome Scalability](https://github.com/binhnguyennus/awesome-scalability) | MIT | `LICENSE` | `data/raw/awesome-scalability` |
| `awesome-cpp` | [Awesome C++](https://github.com/fffaraz/awesome-cpp) | MIT | `LICENSE` | `data/raw/awesome-cpp` |
| `awesome-nodejs` | [Awesome Node.js](https://github.com/sindresorhus/awesome-nodejs) | CC (see LICENSE) | `license` | `data/raw/awesome-nodejs` |
| `awesome-rust` | [Awesome Rust](https://github.com/rust-unofficial/awesome-rust) | CC (see LICENSE) | `LICENSE.txt` | `data/raw/awesome-rust` |
| `github-cheat-sheet` | [GitHub Cheat Sheet](https://github.com/tiimgreen/github-cheat-sheet) | MIT | `LICENSE` | `data/raw/github-cheat-sheet` |
| `awesome-android-ui` | [Awesome Android UI](https://github.com/wasabeef/awesome-android-ui) | MIT | `LICENSE` | `data/raw/awesome-android-ui` |
| `awesome-design-patterns` | [Awesome Design Patterns](https://github.com/DovAmir/awesome-design-patterns) | see upstream | — | `data/raw/awesome-design-patterns` |
| `awesome-java` | [Awesome Java](https://github.com/akullpp/awesome-java) | CC (see LICENSE) | `LICENSE` | `data/raw/awesome-java` |

The engine (`bin/awesome.py`), the plugin adapter (`__init__.py`), the provisioning and
update scripts and the tests are original work, licensed MIT (see `LICENSE`).

List content — README text, link descriptions, section headings — remains under the license
of the respective upstream project. If you redistribute a built index (`index.db`), it
contains derived excerpts of that content; keep this file with it.

License families were detected from the first lines of each upstream license file; consult
the upstream repository for the authoritative text.
