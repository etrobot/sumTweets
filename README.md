# sumTweets

[![Main Workflow](https://github.com/etrobot/sumTweets/actions/workflows/main.yml/badge.svg)](https://github.com/etrobot/sumTweets/actions/workflows/main.yml)

这是一个定时抓取推特合集和账号信息通过AI总结并发生邮件的脚本。

数据来源为推特第三方前端[nitter](https://github.com/zedeus/nitter)，访问[https://status.d420.de](status.d420.de)查看布署站点状态

创建一个.env文件，填入以下信息，再运行
```
OPENAI_API_KEY="sk-*********"
API_BASE_URL="https://*********"
MODEL="openai/gpt-3.5-turbo-1106"
MAILTO="*********@***.***"
MAIL="*********@163.com"
SMTP="smtp.163.com"
MAILPWD="*********"
NITTER="n.biendeo.com"
MINS=20
TARGET='i/lists/1733652180576686386;elonmusk'
INFO='AI/人工智能'
```