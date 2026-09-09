# get-claude-traffic-light (Cloudflare Worker)

Serves `install.sh` from a short, free `*.workers.dev` URL and counts install
attempts (curl requests only — a browser visiting the link doesn't count).

**Deployed and live:** https://get-claude-traffic-light.siddharth-simharaju.workers.dev

## Checking the install count

```bash
curl "https://get-claude-traffic-light.siddharth-simharaju.workers.dev/stats?token=<STATS_TOKEN>"
# {"installs": 12}
```

The token was generated and set as a Worker secret during initial deploy
(`wrangler secret put STATS_TOKEN`) — it isn't in this repo. If you've lost
it, set a new one and redeploy:

```bash
cd worker
npx wrangler secret put STATS_TOKEN
```

## Redeploying after a code change

Only needed when `worker/src/index.js` itself changes — the Worker always
proxies the *live* `install.sh` from GitHub's `main` branch, so changes to
that file need no redeploy.

```bash
cd worker
npx wrangler deploy
```

## Redeploying from scratch (e.g. a new machine, or a fresh account)

```bash
cd worker
npx wrangler login                          # opens your browser
npx wrangler kv namespace create INSTALLS
# paste the printed id into wrangler.toml's kv_namespaces block
npx wrangler secret put STATS_TOKEN         # pick any secret, keep it to yourself
npx wrangler deploy
```

(`wrangler.toml`'s `name` controls the `<name>.<account>.workers.dev`
subdomain — rename it before deploying if you want something different.)

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
