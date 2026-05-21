#!/bin/bash
# Generates /etc/caddy/demos.conf from active demos
DEMOS="/opt/miamipreviewlab/demos"
CONF="/etc/caddy/demos.conf"

> "$CONF"
for d in "$DEMOS"/*/; do
    slug=$(basename "$d")
    [ ! -f "$d/index.html" ] && continue
    cat >> "$CONF" << BLOCK
${slug}.miamipreviewlab.com {
    tls internal
    root * /opt/miamipreviewlab/demos/${slug}
    file_server
    encode gzip
}

BLOCK
done

# Reload Caddy if config changed
caddy reload --config /etc/caddy/Caddyfile 2>/dev/null || systemctl reload caddy
echo "Generated $(grep -c miamipreviewlab.com $CONF) demo blocks"
