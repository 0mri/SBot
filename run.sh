# cd /mnt/c/Users/omri/Desktop/SBot
# sudo -s
source venv/bin/activate 
kill $(ps -ef | grep bot) 
nohup python3 -m bot --dry-run --captcha&
tail -f bot/logs/newegg.log


