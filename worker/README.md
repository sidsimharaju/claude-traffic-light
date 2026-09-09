# get-claude-traffic-light (Cloudflare Worker)

Serves `install.sh` from a short, free `*.workers.dev` URL and counts install
attempts (curl requests only — a browser visiting the link doesn't count).
Already tested end-to-end locally with `wrangler dev` (a fully local, fake
Cloudflare account — no login needed for that part). What's left needs your
real Cloudflare account, so these steps are yours to run:

## 1. One-time setup

```bash
cd worker
npx wrangler login          # opens your browser to authorize — free account is fine
npx wrangler kv namespace create INSTALLS
```

That last command prints an `id`. Paste it into `wrangler.toml`, replacing
`REPLACE_WITH_KV_NAMESPACE_ID`:

```toml
kv_namespaces = [
  { binding = "INSTALLS", id = "<the id it printed>" }
]
```

Then set a secret token for the `/stats` endpoint (pick anything, keep it to
yourself — this is what gates who can read the install count):

```bash
npx wrangler secret put STATS_TOKEN
```

## 2. Deploy

```bash
npx wrangler deploy
```

It prints the live URL — something like
`https://get-claude-traffic-light.<your-account-subdomain>.workers.dev`. That
whole URL is what you share:

```bash
curl -fsSL https://get-claude-traffic-light.<your-account-subdomain>.workers.dev | bash
```

(`wrangler.toml`'s `name` controls the first part of that subdomain — rename
it before deploying if you want something shorter than
`get-claude-traffic-light`, e.g. `get` or `cctl`.)

## Checking the count

```bash
curl "https://get-claude-traffic-light.<your-account-subdomain>.workers.dev/stats?token=<your STATS_TOKEN>"
# {"installs": 12}
```

## Updating install.sh

The Worker always proxies the *live* `install.sh` from the `main` branch on
GitHub — there's nothing to redeploy when that script changes, only when
`worker/src/index.js` itself changes.

## Local testing

```bash
cd worker
echo 'STATS_TOKEN="test-local-token"' > .dev.vars   # gitignored
npx wrangler dev
curl -A curl/8.0 http://localhost:8787/             # counts
curl -A Mozilla/5.0 http://localhost:8787/          # doesn't count
curl "http://localhost:8787/stats?token=test-local-token"
```

Runs against a fully local, fake KV namespace — no real Cloudflare account
touched.
