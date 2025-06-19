#!/bin/bash

# Скрипт для добавления заблокированных доменов в VPN-доступ
# Требует установленного CLI-инструмента `opnvpn_cli`

add_entry() {
  DOMAIN=$1
  NAME=$2
  echo "Добавление: $NAME ($DOMAIN)"
  opnvpn_cli add "$DOMAIN" --name "$NAME"
}

echo "=== Добавление социальных сетей ==="
add_entry "facebook.com" "Facebook"
add_entry "instagram.com" "Instagram"
add_entry "twitter.com" "X (Twitter)"
add_entry "discord.com" "Discord"
add_entry "pinterest.com" "Pinterest"
add_entry "snapchat.com" "Snapchat"

echo "=== Добавление профессиональных платформ ==="
add_entry "linkedin.com" "LinkedIn"

echo "=== Добавление хостинг-провайдеров ==="
add_entry "aws.amazon.com" "Amazon AWS"
add_entry "cloudflare.com" "Cloudflare"
add_entry "digitalocean.com" "DigitalOcean"
add_entry "linode.com" "Linode"
add_entry "ovh.com" "OVH"
add_entry "godaddy.com" "GoDaddy"
add_entry "gcore.com" "GCore"
add_entry "vultr.com" "Vultr"

echo "=== Готово ==="
