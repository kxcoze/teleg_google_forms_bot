# Webhook server for Telegram Bot and Google Forms
Aiohttp-сервер получающий формы Google Forms через webhook и отправляющий полученные данные с помощью Telegram бота в определенный чат.

## Содержание
- [Webhook server for Telegram Bot and Google Forms](#webhook-server-for-telegram-bot-and-google-forms)
  - [Содержание](#содержание)
  - [Инструкция по запуску](#инструкция-по-запуску)
    - [Настройка обратного прокси с помощью Nginx](#настройка-обратного-прокси-с-помощью-nginx)
    - [Настройка Telegram бота](#настройка-telegram-бота)
    - [Настройка Webhook для Google Forms](#настройка-webhook-для-google-forms)

---

## Инструкция по запуску
### Настройка обратного прокси с помощью Nginx
Чтобы сервер мог получать данные от Google Forms и Telegram необходимо настроить обратный прокси на пути `/webhook` и `/form` которые ведут на `http://127.0.0.1:8081`. 

> Если Nginx не установлен на вашей машине, то можно воспользоваться следующими гайдами: [ТЫК](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-20-04-ru), [ТЫК](https://timeweb.cloud/tutorials/ubuntu/kak-ustanovit-nginx-na-ubuntu)

Telegram передает данные только по защищенному соединению, поэтому необходимо получить SSL сертификат на домен, можно воспользоваться бесплатной утилитой **Let's Encrypt**, вот [ГАЙД SSL](https://www.nginx.com/blog/using-free-ssltls-certificates-from-lets-encrypt-with-nginx/) на получение сертификата и установки **cron** задачи по обновлению сертификата.

После утверждения SSL сертификата от **Let's Encrypt**, ключи будут храниться по следующему пути

`/etc/letsencrypt/live/DOMAIN_NAME/fullchain.pem`

`/etc/letsencrypt/live/DOMAIN_NAME/privkey.pem`

где `DOMAIN_NAME` - имя вашего домена

Создаем конфиг для нашего сервера
```sh
sudo nano /etc/nginx/sites-available/DOMAIN_NAME.conf
```

Конфиг для **Nginx** будет иметь такой вид:
```nginx
server {    
    listen              443 ssl;    
    server_name         DOMAIN_NAME;    
    ssl_certificate     /etc/letsencrypt/live/DOMAIN_NAME/fullchain.pem;    
    ssl_certificate_key /etc/letsencrypt/live/DOMAIN_NAME/privkey.pem;    
    
    location /webhook {    
        proxy_set_header Host $http_host;    
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;    
        proxy_redirect off;    
        proxy_buffering off;    
        proxy_pass http://127.0.0.1:8081;    
    }    
    
    location /form {    
        proxy_buffering off;    
        proxy_redirect off;    
        proxy_pass http://127.0.0.1:8081;    
    }    
} 
```

Далее устанавливаем символическую ссылку на конфиг
```
sudo ln -s /etc/nginx/sites-available/DOMAIN_NAME.conf /etc/nginx/sites-enabled/DOMAIN_NAME.conf
```

После этого перезагружаем сервис **Nginx**
```
sudo systemctl restart nginx
```

Чтобы убедиться, что **Nginx** работает правильно, можно попробовать в адресной строке браузера перейти на следующие адреса
`https://DOMAIN_NAME/form` или `https://DOMAIN_NAME/webhook`, они должны выдавать ошибку `502 Bad Gateway`, что говорит о том, что сервер успешно перенаправляет на `http://127.0.0.1:8081` и в данный момент aiohttp сервер не работает.

Желательно создать Whitelist для фаерволла и внести туда IP адреса Google и Telegram:
- [Google](https://support.google.com/a/answer/10026322?hl=en)
- [Telegram](https://core.telegram.org/bots/webhooks#the-short-version)

### Настройка Telegram бота
Клонировать git репозиторий с помощью команды:
```bash
git clone https://github.com/kxcoze/teleg_google_forms_bot
cd teleg_google_forms_bot
```

Создать `.env` файл из `env_dist`
```bash
cp env_dist .env
```

Изменить содержимое файла `.env`
```bash
nano .env
```

Содержание конфига .env
| Переменная | Описание | Вид |
| ---------- | -------- | --- |
|`BOT_TOKEN`| API токен, который берется у [@BotFather](https://t.me/botfather) в Telegram при создании бота | `123456789:AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQq` |
|`ADMIN_IDS`| Список админов, которые будут иметь доступ к логам и командам бота | `[12345678,987654321]` или `[12345678]` |
|`GOOGLE_SECURITY_TOKEN`| Секретное слово для API аутентификации | любая строка, например: `secret-string` |
|`TELEGRAM_SECURITY_TOKEN`| Секретное слово при подключении webhook от Telegram | любая строка, например: `secret-string` |
|`APP_BASE_URL`| URL к домену куда будут отправляться HTTP-запросы от Google и Telegram. **Обязательно https!** | `https://url.to.your.domain` | 
|`DB_NAME`| Имя базы данных | по умолчанию `db` |
|`PROJECT_FIELD`| Название вопроса в Google форме, содержание которого определяет чат для отправки | по умолчанию `Проект` |
|`USERNAME_FIELD`| Название вопроса содержащее ФИО автора содержимого формы | по умолчанию `ФИО` |
|`EXPIRES_DAYS`| Срок годности (в днях) отчета в базе данных, по истечению которого автоматически удалится из БД | по умолчаннию `30` |
|`TIMEZONE`| Временная зона | по умолчанию `Europe/Moscow` |
|`RABBITMQ_USER`| Имя пользователя для RabbitMQ | любая строка, например: `username` или `guest` |
|`RABBITMQ_PASS`| Пароль для пользователя RabbitMQ | любой пароль, например: `s0mEp@ssw0rD999` |
|`RABBITMQ_VHOST`| Имя виртуального хоста для RabbitMQ  | по умолчанию `telegram_bot` |

**ВАЖНО! Перед выполнением следующей команды отправьте вашему новоиспеченному боту команду `/start`, чтобы получать сообщения от него!**

После настройки `.env` файла, далее собираем и запускаем docker контейнеры
```sh
docker-compose up --build -d rabbitmq bot scheduler
```

Если настройка конфигов и запуск прошли успешно, то бот отправит Вам такое сообщение:

![Example 1](https://i.imgur.com/LpRS6sI.png)

### Настройка Webhook для Google Forms
Далее следует настроить вебхук для Google Forms, воспользуемся расширением [**Email Notifications for Google Forms**](https://workspace.google.com/u/0/marketplace/app/email_notifications_for_google_forms/984866591130).

Гиф анимация по установке данного расширения:

![Gif1](https://i.imgur.com/pv0Z3sY.gif)

После установки расширения необходимо создать webhook, который будет привязан к серверу:
1. Заходим в настройки расширения **Email Notifications for Google Forms**
2. Выбираем **Webhooks for Google Forms ➪**
3. Далее нажимаем на кнопку **Create Webhook**
4. В открывшемся окне будет предложено ввести **Webhook name** - имя вебхука, **Request URL** - URL адрес сервера, **Method** - метод HTTP-запроса и остальные настройки
    1. **Webhook name** - можно указать на своё усмотрение
    2. **Request URL** - необходимо обозначить содержимым переменной `APP_BASE_URL` конфига `.env`, но обязательно добавить в конце `/form`, например, если `APP_BASE_URL` равен `https://your-domain.com`, то в **Request URL** надо указать `https://your-domain.com/form`
    3. **Method** - Указывается `POST`
5. Далее во вкладке **Authorization**, необходимо указать тип аутентификации `API Key` и **Add to** - `Header`, после этого в поле **API Key** указываем `security-token` и в поле **API Value** напротив указываем, то значение которое Вы поставили переменной `GOOGLE_SECURITY_TOKEN` конфига `.env`
6. Далее переходим во вкладку **Request Body** и выбираем в **Content Type** - `application/x-www-form-urlencoded`. После этого сформируются готовые поля, однако желательно удалить поля с `Form Id` по `Submitted At`, т.к. эти данные не относятся к содержимому формы
7. Далее сохраняем вебхук нажатием **Save**

![Gif2](https://i.imgur.com/byToWnV.gif)

После создания вебхука необходимо добавить бота в какую-либо группу и отправить форму с указанной группой в форме, например: в конфиге `.env` переменная `PROJECT_FIELD` равна `Проект` и бот добавлен в группу с именем `First Group`

![Bot joined in the group](https://i.imgur.com/p8qwFeY.png)

Далее отправляем форму со следующими данными:

![Google Form example 1](https://i.imgur.com/uq86apa.png)

Если всё настроено успешно, то бот отправит Вам сообщение на подобии этого:

![Teleg bot successfully received](https://i.imgur.com/EsPZjHC.png)

В групповом чате `First Group` появится сообщение от бота

![Teleg bot report to the group](https://i.imgur.com/1Ex95og.png)


