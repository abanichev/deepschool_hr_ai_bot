# DeepSchool AI HR

## Запуск через Docker

```shell
$ git clone git@github.com:abanichev/deepschool_hr_ai_bot.git
Cloning into 'deepschool_hr_ai_bot'...
<...>

$ cd deepschool_hr_ai_bot

$ docker buildx build -t deepschool_hr_ai_bot:v0.1.0 .
[+] Building 1.2s (11/11) FINISHED
<...>

$ cp .env_example .env

$ # PUT YOUR CREDENTIALS INTO .env FILE
$ vim .env

$ docker run --rm -v ./.env:/app/.env deepschool_hr_ai_bot:v0.1.0
2025-10-02 14:42:14,128 - HRBot - INFO - Setting up Together client...
2025-10-02 14:42:14,128 - HRBot - INFO - Together client setup complete.
2025-10-02 14:42:14,129 - HRBot - INFO - Setting up bot...
2025-10-02 14:42:14,256 - HRBot - INFO - Adding bot command handlers...
2025-10-02 14:42:14,256 - HRBot - INFO - Adding bot message handlers...
2025-10-02 14:42:14,257 - HRBot - INFO - Bot setup complete.
2025-10-02 14:42:14,257 - HRBot - INFO - Starting bot...
<...>
```

## Запуск через uv

```shell
$ git clone git@github.com:abanichev/deepschool_hr_ai_bot.git
Cloning into 'deepschool_hr_ai_bot'...
<...>

$ cd deepschool_hr_ai_bot

$ cp .env_example .env

$ # PUT YOUR CREDENTIALS INTO .env FILE
$ vim .env

$ uv sync
Using CPython 3.13.7
Creating virtual environment at: .venv
Resolved 43 packages in 6ms
Installed 41 packages in 41ms
<...>

$ docker run --rm -v ./.env:/app/.env deepschool_hr_ai_bot:v0.1.0
2025-10-02 14:42:14,128 - HRBot - INFO - Setting up Together client...
2025-10-02 14:42:14,128 - HRBot - INFO - Together client setup complete.
2025-10-02 14:42:14,129 - HRBot - INFO - Setting up bot...
2025-10-02 14:42:14,256 - HRBot - INFO - Adding bot command handlers...
2025-10-02 14:42:14,256 - HRBot - INFO - Adding bot message handlers...
2025-10-02 14:42:14,257 - HRBot - INFO - Bot setup complete.
2025-10-02 14:42:14,257 - HRBot - INFO - Starting bot...
<...>

$ uv run app.py
2025-10-02 17:45:24,130 - HRBot - INFO - Setting up Together client...
2025-10-02 17:45:24,130 - HRBot - INFO - Together client setup complete.
2025-10-02 17:45:24,130 - HRBot - INFO - Setting up bot...
2025-10-02 17:45:24,249 - HRBot - INFO - Adding bot command handlers...
2025-10-02 17:45:24,250 - HRBot - INFO - Adding bot message handlers...
2025-10-02 17:45:24,250 - HRBot - INFO - Bot setup complete.
2025-10-02 17:45:24,250 - HRBot - INFO - Starting bot...
<...>
```
