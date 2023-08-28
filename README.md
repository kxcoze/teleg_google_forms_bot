# Webhook server for Telegram Bot and Google Forms
Aiohttp-сервер получающий формы Google Forms через webhook и отправляющий полученные данные с помощью Telegram бота в определенный чат.

---

## Инструкция по запуску
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
![Example 1](https://www.dropbox.com/scl/fi/3xcnw2ckd3vkq2ubymbwf/image1.png?rlkey=4k5irrjmmtzvwvwaywzrnbias&dl=0)

### Настройка Webhook для Google Forms
Далее следует настроить вебхук для Google Forms, воспользуемся расширением [**Email Notifications for Google Forms**](https://workspace.google.com/u/0/marketplace/app/email_notifications_for_google_forms/984866591130).

Гиф анимация по установке данного расширения:
![Gif1](https://www.dropbox.com/scl/fi/8sc3o7lxhsn5vngbyfpce/gif1.gif?rlkey=jazg7c9kfaj3fh7foxmyvx3h5&dl=0)

После установки расширения необходимо создать webhook, который будет привязан к серверу:
![Gif2](https://www.dropbox.com/scl/fi/t1yd5u9939qm9bard1fio/gif2.gif?rlkey=w7a7jzxkk39ba8h27lmsj5xpf&dl=0)

1. Заходим в настройки расширения **Email Notifications for Google Forms**
2. Выбираем **Webhooks for Google Forms ➪**
3. Далее нажимаем на кнопку **Create Webhook**
4. В открывшемся окне будет предложено ввести **Webhook name** -- имя вебхука, **Request URL** -- URL адрес сервера, **Method** -- метод HTTP-запроса и остальные настройки
    1. **Webhook name** -- можно указать на своё усмотрение
    2. **Request URL** -- необходимо обозначить содержимым переменной `APP_BASE_URL` конфига `.env`, но обязательно добавить в конце `/form`, например, если `APP_BASE_URL` равен `https://your-domain.com`, то в **Request URL** надо указать `https://your-domain.com/form`
    3. **Method** -- Указывается `POST`
5. Далее во вкладке **Authorization**, необходимо указать тип аутентификации `API Key` и **Add to** -- `Header`, после этого в поле **API Key** указываем `security-token` и в поле **API Value** напротив указываем, то значение которое Вы поставили переменной `GOOGLE_SECURITY_TOKEN` конфига `.env`
6. Далее переходим во вкладку **Request Body** и выбираем в **Content Type** -- `application/x-www-form-urlencoded`. После этого сформируются готовые поля, однако желательно удалить поля с `Form Id` по `Submitted At`, т.к. эти данные не относятся к содержимому формы
7. Далее сохраняем вебхук нажатием **Save**

После создания вебхука необходимо добавить бота в какую-либо группу и отправить форму с указанной группой в форме, например: в конфиге `.env` переменная `PROJECT_FIELD` равна `Проект` и бот добавлен в группу с именем `First Group`
![Bot joined in the group](https://www.dropbox.com/scl/fi/ixp84vy35nt6ygn24gwp9/image2.png?rlkey=8891e9y060ka0sftx9cvrnq6f&dl=0)
Далее отправляем форму со следующими данными:
![Google Form example 1](https://www.dropbox.com/scl/fi/ixp84vy35nt6ygn24gwp9/image2.png?rlkey=8891e9y060ka0sftx9cvrnq6f&dl=0)
Если всё настроено успешно, то бот отправит Вам сообщение на подобии этого:
![Teleg bot successfully received](https://www.dropbox.com/scl/fi/upvld4p01dok7k7b3bbnm/image4.png?rlkey=yilkmwpbxjw40i9e5vw4qu2sf&dl=0)


