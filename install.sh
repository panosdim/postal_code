#!/bin/sh
if [ "$(id -u)" != "0" ]; then
    exec sudo bash "$0" "$@"
fi

is_service_exists() {
    x="$1"
    if systemctl status "${x}" 2>/dev/null | grep -Fq "Active:"; then
        return 0
    else
        return 1
    fi
}

INSTALL_PATH=/opt/postal
NGINX_CONF_PATH=/etc/nginx/conf.d

# Check if needed files exist
if [ -f postal.service ] && [ -f app.py ] && [ -f data.sqlite ]; then
    # Check if we upgrade or install for first time
    if is_service_exists 'postal.service'; then
        systemctl stop movies.service
        cp app.py $INSTALL_PATH
        systemctl start postal.service
    else
        mkdir -p $INSTALL_PATH
        cp app.py $INSTALL_PATH
        cp data.sqlite $INSTALL_PATH
        cp postal.service /usr/lib/systemd/system
        systemctl start postal.service
        systemctl enable postal.service
        cp postal.conf $NGINX_CONF_PATH
        nginx -s reload
    fi
else
    echo "Not all needed files found. Installation failed."
    exit 1
fi
