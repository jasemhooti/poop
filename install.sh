#!/bin/bash

# رنگ‌ها برای خروجی بهتر
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}به نصب‌کننده ربات شرط‌بندی خوش آمدید!${NC}"
echo "لطفاً یک گزینه را انتخاب کنید:"
echo "1) نصب"
echo "2) بروزرسانی"
echo "3) حذف"
read -p "انتخاب شما: " choice

case $choice in
    1)
        echo -e "${GREEN}شروع فرآیند نصب...${NC}"
        
        # آزادسازی پورت‌ها
        echo "آزادسازی پورت‌های 80 و 443..."
        sudo fuser -k 80/tcp
        sudo fuser -k 443/tcp
        sudo kill -9 $(sudo lsof -t -i:80)
        sudo kill -9 $(sudo lsof -t -i:443)
        
        # توقف سرویس‌های در حال اجرا
        echo "توقف سرویس‌های در حال اجرا..."
        sudo systemctl stop nginx
        sudo systemctl stop apache2
        sudo killall nginx
        sudo killall apache2
        
        # اطمینان از آزاد بودن پورت‌ها
        echo "بررسی آزاد بودن پورت‌ها..."
        if sudo lsof -i :80 > /dev/null; then
            echo -e "${RED}پورت 80 همچنان در حال استفاده است. لطفاً برنامه‌های در حال استفاده از این پورت را ببندید.${NC}"
            exit 1
        fi
        if sudo lsof -i :443 > /dev/null; then
            echo -e "${RED}پورت 443 همچنان در حال استفاده است. لطفاً برنامه‌های در حال استفاده از این پورت را ببندید.${NC}"
            exit 1
        fi
        
        # ایجاد دایرکتوری پروژه
        mkdir -p betting_bot
        cd betting_bot
        
        # ایجاد فایل requirements.txt
        echo "ایجاد فایل requirements.txt..."
        cat > requirements.txt << EOL
aiogram==3.3.0
python-dotenv==1.0.0
mysql-connector-python==8.2.0
cryptography==41.0.7
aiohttp==3.9.1
python-telegram-bot==20.7
EOL
        
        # ایجاد فایل‌های اصلی
        echo "ایجاد فایل‌های اصلی..."
        touch bot.py game.py user_management.py admin_panel.py
        
        # بررسی و نصب پکیج‌های مورد نیاز سیستم
        echo "نصب پکیج‌های مورد نیاز سیستم..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv mysql-server phpmyadmin nginx certbot python3-certbot-nginx
        
        # درخواست اطلاعات مورد نیاز
        read -p "لطفاً توکن ربات تلگرام را وارد کنید: " BOT_TOKEN
        read -p "لطفاً شناسه تلگرام ادمین را وارد کنید: " ADMIN_ID
        read -p "لطفاً دامنه را وارد کنید: " DOMAIN
        
        # تنظیمات Nginx
        echo "تنظیمات Nginx..."
        sudo tee /etc/nginx/sites-available/betting_bot << EOL
server {
    listen 80;
    server_name ${DOMAIN};
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /phpmyadmin {
        include /etc/nginx/snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;
        fastcgi_param SCRIPT_FILENAME \$document_root\$fastcgi_script_name;
        include fastcgi_params;
    }
}
EOL
        
        # فعال‌سازی سایت
        sudo ln -sf /etc/nginx/sites-available/betting_bot /etc/nginx/sites-enabled/
        sudo rm -f /etc/nginx/sites-enabled/default
        
        # بررسی تنظیمات Nginx
        echo "بررسی تنظیمات Nginx..."
        sudo nginx -t
        
        # راه‌اندازی مجدد Nginx
        echo "راه‌اندازی مجدد Nginx..."
        sudo systemctl restart nginx
        
        # تنظیمات SSL
        echo "درخواست گواهینامه SSL..."
        sudo certbot --nginx -d ${DOMAIN} --non-interactive --agree-tos --email admin@${DOMAIN}
        
        # ایجاد محیط مجازی
        echo "ایجاد محیط مجازی Python..."
        python3 -m venv venv
        source venv/bin/activate
        
        # نصب پکیج‌های Python
        echo "نصب پکیج‌های Python..."
        pip install -r requirements.txt
        
        # تنظیمات MySQL
        echo "تنظیمات MySQL..."
        sudo mysql -e "CREATE DATABASE IF NOT EXISTS betting_bot;"
        sudo mysql -e "CREATE USER IF NOT EXISTS 'admin'@'localhost' IDENTIFIED BY 'admin';"
        sudo mysql -e "GRANT ALL PRIVILEGES ON betting_bot.* TO 'admin'@'localhost';"
        sudo mysql -e "FLUSH PRIVILEGES;"
        
        # ایجاد فایل تنظیمات
        cat > .env << EOL
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID
DOMAIN=$DOMAIN
DB_HOST=localhost
DB_USER=admin
DB_PASS=admin
DB_NAME=betting_bot
EOL
        
        # نصب سرویس سیستم
        echo "نصب سرویس سیستم..."
        sudo cp betting_bot.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable betting_bot
        sudo systemctl start betting_bot
        
        echo -e "${GREEN}نصب با موفقیت به پایان رسید!${NC}"
        ;;
        
    2)
        echo -e "${YELLOW}شروع فرآیند بروزرسانی...${NC}"
        cd betting_bot
        source venv/bin/activate
        pip install -r requirements.txt --upgrade
        sudo systemctl restart betting_bot
        echo -e "${GREEN}بروزرسانی با موفقیت به پایان رسید!${NC}"
        ;;
        
    3)
        echo -e "${RED}شروع فرآیند حذف...${NC}"
        sudo systemctl stop betting_bot
        sudo systemctl disable betting_bot
        sudo rm -f /etc/systemd/system/betting_bot.service
        sudo systemctl daemon-reload
        sudo systemctl stop nginx
        sudo systemctl stop apache2
        sudo killall nginx
        sudo killall apache2
        sudo apt-get remove -y phpmyadmin
        sudo mysql -e "DROP DATABASE IF EXISTS betting_bot;"
        sudo mysql -e "DROP USER IF EXISTS 'admin'@'localhost';"
        sudo rm -f /etc/nginx/sites-enabled/betting_bot
        sudo rm -f /etc/nginx/sites-available/betting_bot
        rm -rf betting_bot
        echo -e "${GREEN}حذف با موفقیت به پایان رسید!${NC}"
        ;;
        
    *)
        echo -e "${RED}گزینه نامعتبر!${NC}"
        exit 1
        ;;
esac
