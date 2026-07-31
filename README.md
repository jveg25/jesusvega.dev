# jesusvega.dev

[![CI](https://github.com/jveg25/jesusvega.dev/actions/workflows/ci.yml/badge.svg)](https://github.com/jveg25/jesusvega.dev/actions/workflows/ci.yml)

Personal site — about, work, education, skills, projects. Bilingual
(English / Spanish), light and dark themes.

Static HTML, CSS and ~110 lines of JavaScript. **No build step and no runtime
dependencies**: the files in this repo are exactly what the browser receives.
Python appears only to run the tests, and never ships.

## Layout

```
.
├── index.html          # all the content, in both languages
├── 404.html            # served by Cloudflare Pages for unknown paths
├── styles.css          # palette in :root at the top
├── app.js              # tab switching + language toggle
├── _headers            # security + cache headers (Cloudflare Pages)
├── robots.txt          # crawler policy
├── sitemap.xml         # one URL, both language variants
├── assets/             # photo, favicon, institution logos
├── tests/              # pytest checks — see below
├── pyproject.toml      # test-only dependencies
└── .github/workflows/  # CI
```

There is deliberately **no `.env`** — the site has no secrets, no API keys and
no build configuration. There is no bundler, no framework and no `node_modules`
either. At this size those would add failure modes without buying anything.

## Tests

```bash
uv run pytest
```

A static site has no compiler to catch mistakes, so these tests stand in for
one. They target failures a browser won't announce:

| Check | Why it exists |
|---|---|
| **Translation parity** | Both languages live in the markup and CSS hides one. Forget the Spanish half and that content silently disappears for Spanish readers — no error anywhere. This test names the exact element. |
| **No private identifiers** | The source CV contains a DNI and phone number. Neither belongs on a public page, and both are one careless paste away from returning. |
| **Referenced files exist** | Catches a logo or stylesheet that 404s, including logos set via inline `background-image`. |
| **No placeholder text** | Blocks `[Placeholder]`, `YOUR-USERNAME`, `TODO` reaching production. |
| **CSP hash is current** | `_headers` pins a sha256 of the inline JSON-LD. Edit the JSON without updating the hash and browsers reject the structured data — invisible for months otherwise. The failure message prints the correct hash. |
| **Accessibility basics** | Alt text, `lang` attributes, heading order. |
| **Tabs match panels** | A nav link pointing at a section that doesn't exist. |

CI runs them on every push and pull request.

## How the two languages work

Both languages sit side by side in the markup, and CSS hides whichever isn't
selected:

```html
<p lang="en">Automated the ETL and standardisation of meter measurements…</p>
<p lang="es">Automaticé el ETL y la estandarización de mediciones…</p>
```

For short pieces inside a line, use spans:

```html
<span lang="en">In progress</span><span lang="es">En curso</span>
```

**Anything with no `lang` attribute shows in both** — which is what you want for
names, dates and technology tags. `Python` and `Oct 2023 — Oct 2024` don't need
translating, so they're written once.

Language is chosen in this order: `?lang=es` in the URL, then whatever the
visitor picked last (`localStorage`), then their browser's language. A
Spanish-speaking visitor lands in Spanish without touching anything.

`<body data-lang="en">` is set in the HTML rather than by script, so the page
renders correctly before any JavaScript runs — and stays readable if it never
does.

## Logos

| File | Source |
|---|---|
| `assets/dp600.svg` | Microsoft Learn — official associate-tier certification badge |
| `assets/ucsp.png` | ucsp.edu.pe (`apple-touch-icon`, 180×180, transparent) |
| `assets/uni.png` | Wikimedia Commons — *Uni-logo transparente granate*, downscaled |
| `assets/cambridge.png` | cambridgeenglish.org (`apple-touch-icon`, 280×280) |

All are drawn for light backgrounds, so `.entry-logo.has-logo` puts them on a
white tile — that's what keeps them legible in dark mode. To add one:

```html
<div class="entry-logo has-logo" style="background-image:url(assets/acme.png)"></div>
```

Use `data-monogram="A"` instead to fall back to a letter tile when no decent
logo exists.

## What's deliberately not published

The source CV carries a **DNI and phone number**. Neither is here, and neither
should be: a national ID beside a full name and employer is the raw material for
identity theft, and a public phone number invites SIM-swap attempts. Contact runs
through email, LinkedIn and WhatsApp — all revocable or filterable. A test
enforces this.

## Preview locally

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>. If a change doesn't appear, hard-reload
(<kbd>Cmd</kbd>+<kbd>Shift</kbd>+<kbd>R</kbd>) — browsers cache CSS hard.

`_headers` does nothing locally; it only takes effect once deployed.

## Deploying

### 1. Create the Pages project

Cloudflare dashboard → **Workers & Pages** → **Create** → **Pages** →
**Connect to Git** → pick `jveg25/jesusvega.dev`.

Build settings: framework preset **None**, build command **empty**, output
directory `/`. There is nothing to build.

**Save and Deploy** gives you a `*.pages.dev` URL within a minute.

### 2. Point the domain at it

In the Pages project → **Custom domains** → **Set up a custom domain** →
`jesusvega.dev`. Because the domain is already in your Cloudflare account,
Cloudflare creates the DNS record itself and issues the certificate — you don't
add a record by hand.

Repeat for `www.jesusvega.dev`.

Leave these records **proxied** (orange cloud). That's correct for Pages and is
what Cloudflare sets up. *(This is the opposite of the RAG app's subdomain, which
must be DNS-only so Caddy can obtain its own certificate — don't carry the
setting across.)*

Every push to `main` redeploys automatically.

## Licence

Code is MIT. The biography, work history, portrait photograph and the
third-party logos are **not** — see [LICENSE](LICENSE) for the exact carve-outs.
Reuse the code as a template; bring your own content.

## Still to check

- **WhatsApp link** — `wa.me/jesusvega.dev` uses the username format. Open it
  somewhere your account isn't logged in and confirm it reaches your chat. The
  fallback publishes your phone number, so a working username link matters.
- **Capstone repo must be public**, or the Projects link 404s for visitors.
- **Live demo link** — `personalinstructor.jesusvega.dev` doesn't resolve yet.
  Deploy it or remove the link before sharing the site.
