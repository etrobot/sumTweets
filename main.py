import os,re
from datetime import datetime,timedelta
import pandas as pd
import requests
from bs4 import BeautifulSoup
from litellm import completion
from feedparser import parse
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from markdown import markdown
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

def sendEmail(message:str,receiver:str=os.environ['MAILTO'],subject:str=''):
    '''
    发送邮件的方法
    :param message:
    :param receiver:
    :param subject:
    :return:
    '''
    if len(message)==0:
        return
    message=message.replace('<td','<td style="border:1px solid grey;"').replace('<table','<table style="border-collapse:collapse;"')
    subject=datetime.now().strftime('%Y年%m月%d日')+subject
    sender = os.environ['MAIL'] #发送的邮箱
    receiver = receiver.split(';')  #要接受的邮箱（注:测试中发送其他邮箱会提示错误）
    smtpserver = os.environ['SMTP']
    username = os.environ['MAIL'] #你的邮箱账号
    password = os.environ['MAILPWD'] #你的邮箱密码
    msg = MIMEText(message,'html','utf-8') #中文需参数‘utf-8'，单字节字符不需要
    msg['Subject'] = Header(subject, 'utf-8') #邮件主题
    msg['from'] = sender    #自己的邮件地址
    smtp = smtplib.SMTP()
    try :
        smtp.connect(smtpserver) # 链接
        smtp.login(username, password) # 登陆
        smtp.sendmail(sender, receiver, msg.as_string()) #发送
        print('邮件发送成功')
    except smtplib.SMTPException:
        print('邮件发送失败')
    smtp.quit() # 结束

def sumTweets(prompt:str,lang = '中文',length:int = 10000, model='openai/gpt-3.5-turbo-1106',mail=True,render=True):
    '''
    抓取目标推特AI总结并发邮件
    :param lang:
    :param length:
    :param model:
    :param mail:
    :param render:
    :return:
    '''
    users=os.environ['TARGET']
    info: str = os.environ['INFO']
    nitter:str = os.environ['NITTER']
    minutes:int = int(float(os.environ['MINS']))
    result = ''
    for user in users.split(';'):
        rss_url = f'https://{nitter}/{user}/rss'
        feed = parse(rss_url)
        df = pd.json_normalize(feed.entries)
        df['timestamp'] = df['published'].apply(lambda x: pd.Timestamp(x).timestamp())
        if not 'i/lists' in user:
            df = df.reindex(index=df.index[::-1])
        compareTime = datetime.utcnow() - timedelta(minutes=minutes)
        compareTime = pd.Timestamp(compareTime).timestamp()
        df = df[df['timestamp'] > compareTime]
        if len(df) == 0:
            continue
        for k, v in df.iterrows():
            pattern = r'<a\s+.*?href="([^"]*https://%s/[^/]+/status/[^"]*)"[^>]*>'%nitter.replace(".",r'\.')
            matches = re.findall(pattern, v['summary'])
            if len(matches) > 0:
                if matches[0] in df['id'].values:
                    indices = df[df['id'] == matches[0]]
                    df.at[k, 'summary'] = re.sub(pattern, "<blockquote>%s</blockquote>" % indices['summary'].values[0],
                                                 v['summary'])
                    if 'i/lists' in user:
                        df = df.drop(indices.index)
                else:
                    headers = {
                        'accept-language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6,ja;q=0.5',
                        'User-Agent': "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Mobile Safari/537.36"
                    }
                    session = requests.Session()
                    session.headers = headers
                    oripost = session.get(matches[0]).text
                    quote = BeautifulSoup(oripost, 'html.parser').title.string.replace(" | nitter", '')
                    df.at[k, 'summary'] = re.sub(pattern, "<blockquote>%s</blockquote>" % quote, v['summary'])
        df['content'] = df['published'].str[len('Sun, '):-len(' GMT')] + '[' + df['author'] + ']' + '(' + df[
            'id'].str.replace(nitter, 'x.com') + '): ' + df['summary']
        # df.to_csv('test.csv', index=False)
        tweets = df['content'].to_csv().replace(nitter, 'x.com')[:length]
        if len(prompt)<10:
            prompt =  "<tweets>{tweets}</tweets>\n以上是一些推，你是一名{lang}专栏『{info}最新资讯』的资深作者，请在以上推中，挑选出和『{info}』相关信息(若有)的推,汇编成一篇用markdown排版的{lang}文章，包含发推时间、作者(若有)、推特链接(若有)和推特内容以及你的解读和评论，如果没有{info}相关资讯请回复『NOT FOUND』"
        prompt =  prompt.format(tweets=tweets,lang=lang,info=info)
        print('tweets:', prompt)
        if not 'NOT FOUND' in result:
            result = result + '\n##%s\n\n'%user + completion(model=model, messages=[{"role": "user", "content": prompt, }], api_key=os.environ['OPENAI_API_KEY'],
                       base_url=os.environ['API_BASE_URL'])["choices"][0]["message"]["content"]
    if mail and len(result) > 0:
        if render:
            result=markdown(result.replace('```','').replace('markdown',''),extensions=['markdown.extensions.tables'])
        sendEmail(result)
    return result

if __name__=='__main__':
    sumTweets(os.environ.get('PROMPT',''),mail=True,render=True)