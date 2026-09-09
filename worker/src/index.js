// Cloudflare Worker serving claude-traffic-light's install script from a
// short URL, and counting installs along the way.
//
// GET  /            -> proxies install.sh from GitHub (so `curl -fsSL
//                       <this worker's URL> | bash` works exactly like the
//                       raw GitHub URL did, just shorter and branded).
//                       Only increments the counter for requests that look
//                       like curl (checked via User-Agent) — a browser
//                       visiting the link out of curiosity shouldn't count
//                       as an install attempt.
// GET  /stats?token=... -> returns the current count as JSON. Gated by a
//                       shared-secret query param (set via `wrangler secret
//                       put STATS_TOKEN`) since this is a personal counter,
//                       not something to leave world-readable.
//
// This measures "times someone ran the curl command", not "times the
// install actually succeeded" — that's the same caveat every curl-|-bash
// tool's install count carries; there's no way to know from here whether
// install.sh went on to finish successfully on their machine.

const INSTALL_SCRIPT_URL =
  "https://raw.githubusercontent.com/sidsimharaju/claude-traffic-light/main/install.sh";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/stats") {
      return handleStats(url, env);
    }

    return handleInstall(request, env);
  },
};

async function handleInstall(request, env) {
  const userAgent = request.headers.get("user-agent") || "";
  if (userAgent.toLowerCase().includes("curl")) {
    await incrementCount(env);
  }

  const upstream = await fetch(INSTALL_SCRIPT_URL, {
    cf: { cacheTtl: 300, cacheEverything: true },
  });

  if (!upstream.ok) {
    return new Response(
      "# claude-traffic-light: couldn't fetch install.sh right now — try again shortly, or use:\n" +
        "# curl -fsSL " +
        INSTALL_SCRIPT_URL +
        " | bash\n",
      { status: 502, headers: { "content-type": "text/x-shellscript; charset=utf-8" } },
    );
  }

  const body = await upstream.text();
  return new Response(body, {
    headers: { "content-type": "text/x-shellscript; charset=utf-8" },
  });
}

async function incrementCount(env) {
  const current = await env.INSTALLS.get("count");
  const next = (parseInt(current || "0", 10) + 1).toString();
  await env.INSTALLS.put("count", next);
}

async function handleStats(url, env) {
  const token = url.searchParams.get("token");
  if (!env.STATS_TOKEN || token !== env.STATS_TOKEN) {
    return new Response("Not found", { status: 404 });
  }

  const count = await env.INSTALLS.get("count");
  return new Response(JSON.stringify({ installs: parseInt(count || "0", 10) }), {
    headers: { "content-type": "application/json" },
  });
}
