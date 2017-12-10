## Advanced Python 1117 DZ1(madatory)
## LOG_ANALYZER - парсит логи NGINX сервера на предмет сбора статистики

Запуск :  _python log_analyzer.py \[--conf file\]_

При запуске, если явно не указан конфиг файл, программа ищет его в _/usr/loca/etc/log_analyzer.conf_ , 
если конфиг не обнаружен, программа прерывается.

Формат конфига (секция \[GLOBAL\] обязательна, остальное опционально  ):
```
    [GLOBAL]
    REPORT_SIZE: 1000
    REPORT_DIR: ./reports
    LOG_DIR: ./log
    TS_FILE: /var/tmp/log_analyzer.ts
    #LOG_FILE: log_analyzer.log
```
Если какого-то параметра нет в конфиге, он заменяется параметрами по умолчанию непосредственно из программы.
Скрипт анализирует последний лог файл в директории _"LOG_DIR"_ с названием _"nginx-access-ui.log-20170630\[.gz\]"_
(дата меняется) и генерирует отчет на базе шаблона _report.html_ с названием "report-2017.06.30.html"
(дата соответствует дате в лог файле) и кладет его в директорию _"REPORT_DIR"_.

Отчет содержит таблицу размерa _"REPORT_SIZE"_ со следующими полями:
``` 
count - сколько раз встречается URL, абсолютное значение
count_perc - сколько раз встречается URL, в процентнах относительно общего числа запросов
time_sum - суммарный $request_time для данного URL'а, абсолютное значение
time_perc - суммарный $request_time для данного URL'а, в процентах относительно общего $request_time всех запросов
time_avg - средний $request_time для данного URL'а
time_max - максимальный $request_time для данного URL'а
time_med - медиана $request_time для данного URL'а
```
Таблица упорядочена по убыванию _"time_sum"_


## МОНИТОРИНГ
Скрипт пишет логи в файл, указанный в параметре "LOG_FILE", если не указан, то в консоль вызова. По окончнию (успешному)
работы, скрипт создает (обновляет) ts-файл по пути "TS_FILE" ( _/var/tmp/log_nalyzer.ts_ по умолчанию).
Внутри файлика находится "timestamp" времени окончания работы, "mtime" файлика равен этому таймстемпу


## ТЕСТИРОВАНИЕ
_test_log_analyzer.py_ :  скрипт тестирования
* _python -m unittest -v test_log_analyzer.TestLogAnalyzer.test_check_run_ : тестирует функцию, 
которая отвечает за повторный запуск _log_analyzer.py_ и в случае, если запуск необходим
    возвращает dir() с именами файла лога и репорта, использует TestLogAnalyzer.setUp(), TestLogAnalyzer.tearDown()
* python -m unittest -v test_log_analyzer.TestLogAnalyzer.test_create_report :
    тестирует функцию отвечающую за создание файла репорта из шаблона, в данном случае тестируется реакция на
    exception IOError
* python -m unittest -v test_log_analyzer.TestLogAnalyzer.test_grep_cmd_line :
    conditional skipped
* python -m unittest -v test_log_analyzer.TestLogAnalyzer.test_grep_file :
    проверяет, что функция возвращает dict(), с ссылками в качестве ключей
* python -m unittest -v test_log_analyzer.TestLogAnalyzer.test_read_config :
    тестирует функцию разбирающую initial config и критерием успеха является сравнение
     значений, заданных и считанных, использует TestLogAnalyzer.setUp(), TestLogAnalyzer.tearDown()

## Author
email : savsher@gmail.com
