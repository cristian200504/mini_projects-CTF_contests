#!/bin/sh
set -e
php /seed.php
chown www-data:www-data /var/www/data/phpbb.db
exec apache2-foreground
