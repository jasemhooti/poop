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
        
        # بررسی و نصب پکیج‌های مورد نیاز سیستم
        echo "نصب پکیج‌های مورد نیاز سیستم..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv mysql-server phpmyadmin nginx certbot python3-certbot-nginx
        
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
        
        # درخواست اطلاعات مورد نیاز
        read -p "لطفاً توکن ربات تلگرام را وارد کنید: " BOT_TOKEN
        read -p "لطفاً شناسه تلگرام ادمین را وارد کنید: " ADMIN_ID
        read -p "لطفاً دامنه را وارد کنید: " DOMAIN
        
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
        
        # تنظیمات SSL
        echo "درخواست گواهینامه SSL..."
        sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
        
        # راه‌اندازی سرویس
        echo "راه‌اندازی سرویس..."
        sudo systemctl enable nginx
        sudo systemctl restart nginx
        
        echo -e "${GREEN}نصب با موفقیت به پایان رسید!${NC}"
        ;;
        
    2)
        echo -e "${YELLOW}شروع فرآیند بروزرسانی...${NC}"
        source venv/bin/activate
        pip install -r requirements.txt --upgrade
        echo -e "${GREEN}بروزرسانی با موفقیت به پایان رسید!${NC}"
        ;;
        
    3)
        echo -e "${RED}شروع فرآیند حذف...${NC}"
        sudo systemctl stop nginx
        sudo apt-get remove -y phpmyadmin
        sudo mysql -e "DROP DATABASE IF EXISTS betting_bot;"
        sudo mysql -e "DROP USER IF EXISTS 'admin'@'localhost';"
        rm -rf venv
        rm -f .env
        echo -e "${GREEN}حذف با موفقیت به پایان رسید!${NC}"
        ;;
        
    *)
        echo -e "${RED}گزینه نامعتبر!${NC}"
        exit 1
        ;;
esac 