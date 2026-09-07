FROM php:8.2.29-apache

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends unzip; \
    rm -rf /var/lib/apt/lists/*; \
    curl -fsSL -o /tmp/phpbb.zip https://download.phpbb.com/pub/release/3.3/3.3.16/phpBB-3.3.16.zip; \
    echo "f3abb3f28ec50b71702edab936e6e1f288d3f1697e131f4427143b72b68f1eee  /tmp/phpbb.zip" | sha256sum -c -; \
    unzip -q /tmp/phpbb.zip -d /tmp; \
    rm -rf /var/www/html /tmp/phpbb.zip; \
    mv /tmp/phpBB3 /var/www/html; \
    sed -i 's/^Listen 80$/Listen 8080/' /etc/apache2/ports.conf; \
    sed -i 's/:80>/:8080>/' /etc/apache2/sites-available/000-default.conf

COPY install-config.yml /tmp/install-config.yml
COPY seed.php /seed.php
COPY entrypoint.sh /entrypoint.sh

RUN set -eux; \
    mkdir -p /var/www/data; \
    sed -i "s|__ADMIN_PASSWORD__|$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 24)|" /tmp/install-config.yml; \
    php /var/www/html/install/phpbbcli.php install /tmp/install-config.yml; \
    rm -rf /var/www/html/install /tmp/install-config.yml; \
    chmod +x /entrypoint.sh; \
    chown -R www-data:www-data /var/www/html /var/www/data

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
