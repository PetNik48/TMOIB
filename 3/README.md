# Практическое задание

Обнаружение вредоносного программного обеспечения (ВПО)

## Задача

Обучить модель машинного обучения для обнаружения ВПО на основе открытых наборов данных

## Датасеты

* [SOREL](https://github.com/sophos/SOREL-20M)
* [Malimg](https://github.com/jenseWang/malware-dataset-Malimg) 
* [MaleX](https://github.com/Mayachitra-Inc/MaleX) 
* [MTA-KDD-19](https://github.com/IvanLetteri/MTA-KDD-19) 
* [BODMAS](https://github.com/jenseWang/malware-dataset-Malimg) 
* [Android Malware dataset](https://github.com/aleguma/kronodroid) 
* [BIG Malware Dataset from Microsoft ](https://srv.secdev.space:8443/s/gokzfMkYC9rxtQ7) 
* [Ember](https://github.com/elastic/ember) 

## Требуется

0. Разбиться на команды по 2-3 человека и внести в [таблицу](https://1drv.ms/x/s!Ap1Ijs338IQ9gYNumn0zvg7ty_Okpw?e=fPmRIN) данные  
1. Выбрать датасет
2. Провести его анализ с визуализацией
3. Выбрать признаки для МО
4. Обучить модель, провести кроссвалидацию
5. Подготовить ноутбук с результатами и оценками по метрикам (accuracy, precision, recall, f1-measure)

 > Загружать нужно будет ноутбук, который можно будет выполнить, начиная с загрузки датасета на сервер с юпитером. Пример неполного [отчета](https://srv.secdev.space/mirea-bbmo/prz3/-/blob/main/prz-malware-example.ipynb)

## Загрузка результатов
Результат нужно будет загрузить в gitlab

```
cd work
git clone https://srv.secdev.space/mirea-bbmo/prz3.git
git add GROUP-FIO-FIO-FIO-DATASET.ipynb
git push
```

## Срок сдачи практики

**19 апреля 2023 года**
