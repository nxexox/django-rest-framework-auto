# [Django REST Framework AUTO](https://github.com/nxexox/django-rest-framework-auto)
DPF-Auto - это мощный и гибкий инструмент для легкого создания мощных Web APIs.

# Описание

DPF-Auto - это мощный и гибкий инструмент для легкого создания мощных Web APIs.
Мы умеем:

 - Автоматическое формирование документации вашего API для фронт разработчиков. Документация формируется не в html документах, а во view, который можно повесить на ссылку и настроить многие вещи. Идея была позаимствована и развита у [drfdocs.com](https://www.drfdocs.com/), за что ему большая благодарность.
 - Автоматическое тестирование вашего API. Полное тестирование всей схемы API, на предмет соответствия документации, принимаемых возвращаемых данных, соответствия поведению с ошибками, соответствия схеме JSON.
 - Помощь в написании view для API. Помощь в обработке ошибок, простая и гибкая система работы с входящими данными и исходящими данными. Помогает с легкостью держать единую схему JSON как на всем проекте, так и на отдельных блоках проекта. Позволяет создать свою единую базу ошибок, и кодов ошибок, возвращаемых клиенту.
 - Разные полезные утилиты, которые были позаимствованы из разных протоколов, разных утилит, и разных реализаций. Пример: `GraphQLField`.

Этот пакет не является полноценно самостоятельным для построения REST API. Это доработка вокруг [django-rest-framework.org](https://www.django-rest-framework.org/) позволяющая писать ваше API еще проще и еще мощнее.

# Зависимости
 -   Python (3.4, 3.5, 3.6)
 -   Django (1.9, 1.10, 1.11)
 -   DjangoRestFramework (3)
# Установка
Установка через  `pip`...
```
pip install git+https://github.com/nxexox/django-rest-framework-auto.git
```
Добавить `'drf_auto'`  в ваши  `INSTALLED_APPS`  в настройках.
```
INSTALLED_APPS = (
    ...
    'drf_auto',
)
```
# Примеры
Давайте рассмотрим примеры использования по порядку.
 - [x] Документация.
 - [x] Написание View.
 - [ ] Тестирование.
 - [ ] Комбинирование для упрощения кода.
 - [x] Настройки.
 - [x] Обработка ошибок.

## АвтоДокументация
Для начала напишите свое первое view и зарегистрируем его в роутере.
```python  
class TestView(APIView):
	"""
	Тестовый поинт, для проверки работы автодокументации.
	"""  
	http_method_names = ['get', 'post', 'put', 'delete'] 
	docs_serializer_classes = { 
		'get': GetExampleSerializer, 
		'post': { 
			'in': PostInExampleSerializer, 
			'out': PostOutExampleSerializer 
		}
	}
	docs_exclude_fields = {
		'post': ['exclude_field', 'exclude_field_two']
	}
```
`GetExampleSerializer, PostInExampleSerializer, PostOutExampleSerializer` - любые стандартные `rest_framework.serializers.Serializer, rest_framework.serializers.ModelSerializer`, используются для примера.
Затем нужно подключить view с документацией в роутер.
```python
from django.conf.urls import url, include
from test_app.views import TestView
from drf_auto.views import DRFDocsView

urlpatterns = [
	url(r'^test-view/$', TestView.as_view()),
    url(r'^api-docs/$', DRFDocsView.as_view(), name='docs')
]
## OR ##
from drf_auto import urls as api_docs_urls

urlpatterns = [
	url(r'^test-view/$', TestView.as_view()),
	url(r'^api-docs/', include(api_docs_urls))
]
```
После этого можно открывать страницу `api-docs` и там будет динамически сгенерирована документация. Обратите внимание, в первом случае мы указывали `name='docs'`, а во втором нет. Во втором случае `name='docs'` уже указано внутри `api_docs_urls`. Не беспокойтесь, параметрами `name, namespace` можно управлять через настройки.
Если вы добавите еще несколько разных view, то автодока их все подтянет и отобразит. Главное что бы они были зарегистрированы в `urls` проекта.
Для управления отображения в автодокументации поинтов и описания, нужно разобраться как работает автодока.

 - В базовое описание поинта попадает `__doc__` `view` объекта, т.е. класса. 
 - В описание каждого метода попадает `__doc__` каждого метода. Если мы реализуем метод `get` у `TestView` тогда в описании метода `get` будет эта документация. Тут лучше всего описывать `url` параметры вида `(?P<pk>\d+)`.
 - Блоки `Принимает`/`Возвращает` формируются благодаря дополнительному полю `docs_serializer_classes`. Где ключом является метод, а значением является описание метода через сериалайзеры. Есть несколько вариантов использования словаря:
 - - Указать метод и один сериалайзер: `'get': GetExampleSerializer`. В таком случае в блок `Возвращает` попадет описание этого сериалайзера. Автодокументация возьмет все филды и опишет их. Тип филда, подпись (`label` или `verbose_name`) в зависимости от типа филда. В блок `Принимает` не попадет ничего, и он просто не отобразиться в документации.
 - - Указать метод и точное описание метода. 
	```python
	'post': { 
		'in': PostInExampleSerializer, 
		'out': PostOutExampleSerializer 
	}
	```
    В таком случае в блок `Принимает` попадет описание `PostInExampleSerializer` сериалайзера. А в блок `Возвращает` попадет описание `PostOutExampleSerializer` сериалайзера. Так же, можно указать только один из двух ключей `in`/`out`. В таком случае только один ключ попадет в документацию, а второй будет игнорирован и исключен из документации.
 - - Не описывать метод вовсе. В таком случае блоки `Принимает`/`Возвращает` будут исключены, и вместо них будет блок `ALL`. Содержимое его будет описанием сериалайзера из атрибута `serializer_class`. Если таковой установлен. Т.е. автодока сама попытается найти сериалайзер для отображения документации.
 - Дополнительно можно во view установить атрибут `docs_exclude_fields`. Это словарь, где ключ метод, значение список филдов. Эти филды для этого метода будут исключены из документации. Например вы хотите давать пользователю создавать статью, но привязку пользователя к статье брать из `request.user`, в таком случае просто искчлючите из документации филд пользователя, а самостоятельно пробрасывайте его в данные перед созданием.
 - Есть еще одна полезная вещь для описания документации сериалайзеров. Если у вас в сериалайзере используется `serializers.SerializerMethodField`, вы можете описать автоматически и его. Для этого в сериалайзере с таким методом, нужно прописать `class Meta`, внутри него описать атрибут `doc_method_fields_classes` который является словарем. Где ключ это название филда, а значение, это готовый сериалайзер, из которого можно сформировать документацию. В таком случае этот метод будет описан этим сериалайзером. Пример: 
	```python
	class DocsSerializer(rest_framework.serializers.Serializer):
		test = rest_framework.serializers.CharField(label='Какое то описание')


	class TestSerializer(rest_framework.serializers.Serializer):
	    test_field = rest_framework.serializers.SerializerMethodField()
	    
	    class Meta:
		    doc_method_fields_classes = {
				'test_field': DocsSerializer
			}
		
	    def get_test_field(self, obj):
		    return {'test': 'result'} 
	```
## Написание View
Для полноценного использования всех возможностей `DRF-Auto`, писать `view` нужно через классы, и наследоваться от `DRF-Auto views`.
Есть несколько базовых классов. Все находятся в `drf_auto.views.rest`:
 - `AutoPointFailRequest(rest_framework.generics.GenericAPIView)` - Класс для удобной работы с ошибками во время обработки запроса.
 - `AutoSearchSerializerView(AutoPointFailRequest)` - Класс для поиска сериалайзера для обработки данных. Используется в обработке запроса и ответа.
 - `AutoResponseSerializerView(AutoSearchSerializerView)` - Класс для автоматического формирования ответа от поинта.
 - `AutoRequestSerializerView(AutoPointFailRequest)` - Класс для помощи в обработке запроса.
 - `RestAPIView(AutoRequestSerializerView, AutoResponseSerializerView)` - Базовый класс для всех рест апи, которые вы будете использовать.
 - `RestListAPIView(AutoRequestSerializerView, rest_framework.generics.ListAPIView, AutoResponseSerializerView)` - Generic `view` class для списка.
 - `RestRetrieveAPIView(AutoRequestSerializerView, rest_framework.generics.RetrieveAPIView, AutoResponseSerializerView)` - Generic `view` class, для конкретного объекта.
 - `RestUpdateAPIView(AutoRequestSerializerView, rest_framework.generics.UpdateAPIView, AutoResponseSerializerView)` - Generic `view` class для изменения объекта.
 - `RestCreateAPIView(AutoRequestSerializerView, rest_framework.generics.CreateAPIView, AutoResponseSerializerView)` - Generic `view` class для создания объекта.
 - `RestDestroyAPIView(AutoRequestSerializerView, rest_framework.generics.DestroyAPIView, AutoResponseSerializerView)` - Generic `view` class для удаления объекта.
 
### AutoPointFailRequest
 Класс предоставляет метод `fail(status, code=None, message=None, data=None, fields=None)` который формирует и возвращает объект Response с ошибкой обработки запроса. Про обработку ошибок читайте [`тут`](https://google.com). Так же класс автоматически ловит и обрабатывает исключения в любом месте обработки запроса. Исключения ловит только `drf_auto.exceptions.FailPointRequest, rest_framework.serializers.ValidationError`. Если он увидел такое исключение, тогда он формирует и возвращает соответствующий объект ответа.
  - `status` - Код ответа сервера.
  - `code` - Код ответа в JSON. на верхнем уровне в объекте `code`. Если не указан, принимает значение status.
  - `message` - Сообщение которое следует вернуть. Если не указано, тогда пытается найти его в общем словаре описания ошибок, по ключу `code`. Про общий словарь читайте в [`настройках`](https://google.com).
  - `data` - Дополнительные данные которые необходимо вернуть, в любом JSON серилизуемом формате. Если не указано, то ключ `data` в ответе отсутствует.
  - `fields` - Словарь филдов, для управления ответом.  Ключ это ключ который вернется, значение, это ключ из стандартного набора атрибутов. Пример: `{'response_code': 'code', 'response_message': 'message'}`. В таком случае ответ всегда будет фиксирован и выглядеть так: `{'response_code': code, 'response_message': message}`.

В стандартном случае ответ ошибки выглядит так:
 ```json
{
	'code': code, 
	'message': message, 
	'data': data
}
 ```
 
### AutoSearchSerializerView
 Этот класс помогает искать сериалайзер для обработки ответа или запроса. Предоставляет метод `get_serializer_class(is_response=False)`, с помощью которого и происходит поиск. 
 - `is_response` - Флаг, указывающий это поиск сериалайзера для формирования ответа, или обработки запроса?

Так же имеет ряд атрибутов настроект. По дефолту они настроены данными из настроек приложения, но для каждого поинта можно их менять.
 - `serializers_response_field` - Название филда, для поиска словаря сериалайзеров для ответа. Дефолтное: `serializer_classes`.
 - `serializers_request_field` - Название филда, для поиска словаря сериалайзеров для обработки запроса. Дефолтное: `serializer_classes`.
 - `serializers_request_key` - Ключ используются для поиска внутри сериалайзеров. request_key - обработка водящих данных. Дефолтное: `in`.
 - `serializers_response_key` - Ключ используются для поиска внутри сериалайзеров. response_key - обработка ответа сервера. Дефолтное: `out`.

### AutoResponseSerializerView
Этот класс предоставляет метод `get_response(code, serializer=None, data=None, is_serializer=False, serializer_class=None, many=False, *args, **kwargs)` который формирует и возвращает объект ответа. Методу можно как отдавать готовые серилизованные данные так и необработанные данные и просить обработать сериалайзером. Он сам подберет сериалайзер в зависимости от настроек `view` и сформирует ответ.
 - `code` - Код ответа сервера.
 - `serializer` - Сериалайзер который уже хранит данные.
 - `data` - Данные, которые будут возвращены в ответе.
 - `is_serializer` - Флаг, указывающий нужно ли серилизовать данные или они уже готовы к ответу.
 - `serializer_class` - Класс сериалайзера которым нужно обработать данные. Если указан, тогда обработка будет этим сериалайзером.
 - `many` - Флаг указывающий, это один объект нужно обработать, или множество объектов нужно обработать сериалайзером.

### AutoRequestSerializerView
Этот класс позволяет менять данные в запросе, до его обработки. Так же немного переопределяет логику поиска сериалайзера для обработки запроса.
`get_initial_data(data)` метод позволяет менять данные в запросе.
 - `data` - Данные, пришедшие в запросе.

Для работы с `DRF-Auto` достаточно унаследоваться от `RestAPIView` или любого Generic `view` класса.

## Настройки
Настройки приложения прописаны в `settings.py` вашего проекта.
Установите атрибут `REST_FRAMEWORK_AUTO` в `settings.py`. `REST_FRAMEWORK_AUTO` - Это словарь.
Пример:
```python
# ... your other settings
REST_FRAMEWORK_AUTO = {
	'HIDE_DOCS': True,
	'SERIALIZERS_ATTR_NAME': 'docs_serializer_classes',
	'EXCLUDE_FIELDS_ATTR_NAME': 'docs_exclude_fields',
	'SERIALIZER_DOC_ATTR': 'doc_method_fields_classes',
	'SERIALIZER_DOC_CODES': {'common': {}, 'specific': {}},
	'SERIALIZERS_RESPONSE_FIELD': 'serializer_classes',
	'SERIALIZERS_REQUEST_FIELD': 'serializer_classes',
	'SERIALIZERS_REQUEST_KEY': 'in',
	'SERIALIZERS_RESPONSE_KEY': 'out'
}
# ... your other settings
```

 - `HIDE_DOCS` - Скрыть ли документацию. Нужно например что бы скрывать документацию апи для разработчиков на продакшн стенде.
 - `SERIALIZERS_ATTR_NAME` - Название атрибута, который будет уставновлен на всех view, для поиска словаря с описанием сериалайзеров для документации.
 - `EXCLUDE_FIELDS_ATTR_NAME` - Название атрибута для исключения филдов из описания документации.
 - `SERIALIZER_DOC_ATTR` - Название атрибута для описания `SerialiazerMethodField` у сериалайзеров. Прописывать в `serializer.Meta` классе. Даже если класс не `ModelSerializer`.
 - `SERIALIZER_DOC_CODES` - Единая база ошибок.
 - `SERIALIZERS_RESPONSE_FIELD` - Название филда, для поиска словаря сериалайзеров для ответа.
 - `SERIALIZERS_REQUEST_FIELD` - Название филда, для поиска словаря сериалайзеров для обработки запроса.
 - `SERIALIZERS_REQUEST_KEY` - Ключ используются для поиска внутри сериалайзеров. request_key - обработка водящих данных. Дефолтное: `in`.
 - `SERIALIZERS_RESPONSE_KEY` - Ключ используются для поиска внутри сериалайзеров. response_key - обработка ответа сервера. Дефолтное: `out`.

## Обработка ошибок
Сообщить клиенту про ошибку, можно двумя способами:

 - Использовать метод `fail(status, code=None, message=None, data=None, fields=None, *args, **kwargs)` у `view` класса. Он формирует и возвращает `Response`, потому его результат нужно возвращать из `view.`
 - Выбросить исключение `drf_auto.exceptions.FailPointRequest(status, code=None, message=None, data=None, fields=None, *args, **kwargs)`. Исключение имеет точно такую же сигнатуру что и `fail`. По сути, `fail` является оберткой над `FailPointRequest`. В случае исключения, его можно бросать в любом месте запроса, тогда он будет пойман базовым классом и обработается как следует.

Сигнатура:
  - `status` - Код ответа сервера.
  - `code` - Код ответа в JSON. на верхнем уровне в объекте `code`. Если не указан, принимает значение status.
  - `message` - Сообщение которое следует вернуть. Если не указано, тогда пытается найти его в общем словаре описания ошибок, по ключу `code`.
  - `data` - Дополнительные данные которые необходимо вернуть, в любом JSON серилизуемом формате. Если не указано, то ключ `data` в ответе отсутствует.
  - `fields` - Словарь филдов, для управления ответом.  Ключ это ключ который вернется, значение, это ключ из стандартного набора атрибутов. Пример: `{'response_code': 'code', 'response_message': 'message'}`. В таком случае ответ всегда будет фиксирован и выглядеть так: `{'response_code': code, 'response_message': message}`.

В стандартном случае ответ ошибки выглядит так:
 ```json
{
	'code': code, 
	'message': message, 
	'data': data
}
 ```
 Общий словарь ошибок можно сформировать в настройках. Либо в другом месте и в настройках его пробросить. Пример:
```json
{
	'common': {  
	    '1**': 'Проблемы с правами на объект.',  
		'2**': 'Не найдено.',  
		'3**': 'Пока пусто',  
		'4**': 'Неверный запрос.'  
	},  
	'specific': {  
	    '100': 'У вас нет прав на просмотр объекта. Пожалуйста убедитесь в верности запрашиваемых данных.',  
		'101': 'У вас нет прав на удаление объекта. Пожалуйста убедитесь в верности запроса.',  
		'102': 'У вас нет прав на создание объекта. Пожалуйста убедитесь в верности запроса.',  
		'200': 'Не найден родительский объект. Возможно он был удален или у вас не хватает прав.',  
		'400': 'Плохой запрос. Неверные данные.',  
		'401': 'Ошибка валидации.',  
	}
}
```
Этот словарь отразиться в авто документации по апи. `common` секция используется только для автодоки. Секция `specific` используется как для автодоки, так и для поиска сообщения в ответе, когда произошла ошибка. Сообщение ищется по параметру `code` у исключения `drf_auto.exceptions.FailPointRequest`. Найденное сообщение попадет в `message` ответа сервера.

# Поддержка
По всем вопросам поддержки, создавайте issue или пишите разработчикам на почту.
Проект в альфа версии, и потихоньку будет дорабатываться и улучшаться.
