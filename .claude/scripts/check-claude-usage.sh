#!/bin/bash
# Check Claude Max plan usage via the internal OAuth usage API
# Reads credentials from ~/.claude/.credentials.json

# Token source priority: CLAUDE_CODE_OAUTH_TOKEN env var (setup-token / alt accounts),
# then $CLAUDE_CONFIG_DIR/.credentials.json, then $CLAUDE_CONFIG_DIR/.oauth-token
# (alt-account dirs store a bare setup-token there and have no .credentials.json;
# Claudian doesn't pass CLAUDE_CODE_OAUTH_TOKEN through to subshells, so this is
# how an in-session run on an alt account finds its token), then ~/.claude/.
if [ -n "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
  TOKEN="$CLAUDE_CODE_OAUTH_TOKEN"
else
  CONF_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
  if [ -f "$CONF_DIR/.credentials.json" ]; then
    TOKEN=$(node -e "const c=JSON.parse(require('fs').readFileSync('$CONF_DIR/.credentials.json','utf8'));console.log(c.claudeAiOauth?.accessToken||'')")
  elif [ -f "$CONF_DIR/.oauth-token" ]; then
    TOKEN=$(cat "$CONF_DIR/.oauth-token")
  fi
  if [ -z "$TOKEN" ]; then
    echo "Error: No token found (checked \$CLAUDE_CODE_OAUTH_TOKEN, $CONF_DIR/.credentials.json, $CONF_DIR/.oauth-token)"
    echo "Set CLAUDE_CODE_OAUTH_TOKEN, or log into Claude Code."
    exit 1
  fi
fi

RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "anthropic-beta: oauth-2025-04-20" \
  "https://api.anthropic.com/api/oauth/usage")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" != "200" ]; then
  # Setup-tokens (lent/alt accounts) lack the user:profile scope, so the OAuth
  # usage endpoint 403s permanently for them. Fallback: make a minimal 1-token
  # haiku call and read the anthropic-ratelimit-unified-* response headers —
  # the same Pro/Max subscription meter, but only 5h/7d totals + overage status
  # (no per-model weekly breakdown, no credit spend).
  HDRS=$(curl -s -D - -o /dev/null -X POST "https://api.anthropic.com/v1/messages" \
    -H "Authorization: Bearer $TOKEN" \
    -H "anthropic-beta: oauth-2025-04-20" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d '{"model":"claude-haiku-4-5","max_tokens":1,"messages":[{"role":"user","content":"hi"}]}' | tr -d '\r')

  if ! printf '%s\n' "$HDRS" | grep -qi '^anthropic-ratelimit-unified-'; then
    echo "Error: usage API returned HTTP $HTTP_CODE, and the rate-limit-header fallback got no unified headers either."
    echo "Usage API body: $BODY"
    echo "Fallback response status: $(printf '%s\n' "$HDRS" | head -1)"
    exit 1
  fi

  if [ "${1}" = "--raw" ]; then
    printf '%s\n' "$HDRS" | grep -i '^anthropic-ratelimit-unified-'
    exit 0
  fi

  node -e "
const lines = process.argv[1].split('\n');
const h = {};
for (const l of lines) {
  const m = l.match(/^anthropic-ratelimit-unified-(.+?):\s*(.*)$/i);
  if (m) h[m[1].toLowerCase()] = m[2].trim();
}
const pct = (v) => v == null ? '—' : (Number(v) * 100).toFixed(1) + '%';
const when = (s, dateOnly) => {
  if (!s) return '—';
  const d = /^\d+\$/.test(s) ? new Date(Number(s) * 1000) : new Date(s);
  if (isNaN(d)) return s;
  return dateOnly ? d.toLocaleDateString() : d.toLocaleTimeString();
};
const row = (label, value, note) => console.log(label.padEnd(16) + value + (note ? '  ' + note : ''));

console.log('═══ Claude Usage ═══  (from rate-limit headers; 5h/7d only — no per-model/credit breakdown)');
console.log();
const flag = (k) => h[k] && h[k] !== 'allowed' ? ' [' + h[k] + ']' : '';
row('5-hour window:', pct(h['5h-utilization']) + flag('5h-status'), '(resets ' + when(h['5h-reset']) + ')');
row('7-day window:', pct(h['7d-utilization']) + flag('7d-status'), '(resets ' + when(h['7d-reset'], true) + ')');
if (h['overage-status']) {
  row('Overage:', h['overage-status'], h['overage-disabled-reason'] ? '(' + h['overage-disabled-reason'] + ')' : '');
}
// Surface any additional unified utilization headers (e.g. future per-model ones)
const known = ['5h-utilization','5h-reset','5h-status','7d-utilization','7d-reset','7d-status',
  'overage-status','overage-disabled-reason','status','fallback-percentage','representative-claim','reset'];
for (const k of Object.keys(h)) {
  if (!known.includes(k)) row(k + ':', h[k]);
}
console.log();
" "$HDRS"
  exit 0
fi

# Raw JSON for debugging (pass --raw flag)
if [ "${1}" = "--raw" ]; then
  echo "$BODY" | node -e "process.stdin.setEncoding('utf8');let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.stringify(JSON.parse(d),null,2)))"
  exit 0
fi

# Parse and display with node
node -e "
const d = JSON.parse(process.argv[1]);
const pct = (v) => v == null ? '—' : Number(v).toFixed(1) + '%';
const when = (s, dateOnly) => !s ? '—' : (dateOnly ? new Date(s).toLocaleDateString() : new Date(s).toLocaleTimeString());
const sym = { USD: '\$', EUR: '€', GBP: '£' };
const limits = Array.isArray(d.limits) ? d.limits : [];
const byKind = (k) => limits.filter(l => l.kind === k);
const row = (label, value, note) => console.log(label.padEnd(16) + value + (note ? '  ' + note : ''));

console.log('═══ Claude Usage ═══');
console.log();

// 5-hour / session window
const session = byKind('session')[0];
if (session || d.five_hour) {
  const s = session || d.five_hour;
  row('5-hour window:', pct(session ? s.percent : s.utilization), '(resets ' + when(s.resets_at) + ')');
}

// 7-day overall
const weekly = byKind('weekly_all')[0];
if (weekly || d.seven_day) {
  const s = weekly || d.seven_day;
  row('7-day window:', pct(weekly ? s.percent : s.utilization), '(resets ' + when(s.resets_at, true) + ')');
}

// Per-model 7-day windows (Fable, Opus, Sonnet, … — whatever the API reports)
const scoped = byKind('weekly_scoped');
for (const s of scoped) {
  const m = s.scope && s.scope.model;
  const name = (m && (m.display_name || m.id)) || (s.scope && s.scope.surface) || 'scoped';
  row('7-day ' + name + ':', pct(s.percent), '(resets ' + when(s.resets_at, true) + ')');
}
// Legacy fallback for the old top-level per-model fields
if (!scoped.length) {
  for (const [k, label] of [['seven_day_opus','Opus'],['seven_day_sonnet','Sonnet']]) {
    if (d[k]) row('7-day ' + label + ':', pct(d[k].utilization));
  }
}

// Extra usage credits — amounts come back in minor units (cents)
const sp = d.spend;
if (sp && sp.enabled && sp.used && sp.limit) {
  const cur = sym[sp.used.currency] || (sp.used.currency + ' ');
  const amt = (m) => cur + (m.amount_minor / Math.pow(10, m.exponent)).toFixed(2);
  row('Extra usage:', pct(sp.percent), '(' + amt(sp.used) + ' / ' + amt(sp.limit) + ')');
} else if (d.extra_usage && d.extra_usage.used_credits != null) {
  const e = d.extra_usage;
  const dp = e.decimal_places == null ? 2 : e.decimal_places;
  const cur = sym[e.currency] || ((e.currency || '') + ' ');
  const amt = (v) => v == null ? '?' : cur + (v / Math.pow(10, dp)).toFixed(2);
  row('Extra usage:', pct(e.utilization), '(' + amt(e.used_credits) + ' / ' + amt(e.monthly_limit) + ')');
}

console.log();
" "$BODY"
