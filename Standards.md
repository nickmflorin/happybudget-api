# HappyBudget API Standards & Conventions

### The Zen of Python

```bash
Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
Readability counts.
Special cases arent special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
Now is better than never.
Although never is often better than *right* now.
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
```

## Importing Modules, Packages & Files

### Import Order

Following a consistent and standardized module/package importing order makes it
easier to quickly and easily evaluate the dependencies of a given file and search
for similar uses of a given import throughout the project.

In our project, we strictly require that the following guidelines be used when
ordering module-level or package level imports in a Python file.

#### Import Groups

Imports should be organized by groups, with the groups that an import can belong
to outlined below. Each group should be separated by a line break unless there
are only a few imports in the file. In this case, a line break separating the
groups is not necessary.

##### Group Ordering:

The import groups themselves should be ordered based on the order of the
definitions in the next second. Additionally, the imports within each group
should be ordered based on the following criteria:

###### Alphabetical

Imports within a group should be alphabetized.

```python
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
```

In the above example, conf is alphabetically before contrib, and fields is
alphabetically before models.

###### Nested Levels

If imports within a group share a common module, the more specific modules
should be imported after the more general modules.

```python
from happybudget.lib.utils import ensure_iterable, get_nested_attribute
from happybudget.lib.utils.urls import parse_ids_from_request
```

##### Groups

Imports should be grouped by the following definitions. These group definitions
are ordered, so the grouped imports should follow the same order that the groups
are defined in.

1. Absolute Imports from Global Third-Party Packages
2. Absolute Imports from Django Modules
3. Absolute Imports from Django REST Framework & Related Modules
4. Absolute Imports from lib or conf (when inside of app, which you will be the majority of the time).
5. Absolute Imports from app (when inside of app, which you will be the majority of the time).
6. Relative Imports

###### Global Third-Party Packages

Imports of Python system and application installed packages excluding imports
from `django`, `rest_framework`, or `rest_framework` related packages
(like `rest_framework_simplejwt`).

```python
import datetime
import os
import time
```

###### Django Modules

Imports from django modules.

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, IntegrityError

###### Django REST Framework Modules

Imports from `rest_framework` modules or related packages.

```python
from rest_framework import views, exceptions, viewsets, serializers, generics
from rest_framework.serializers import as_serializer_error
from rest_framework_simplejwt.exceptions import AuthenticationFailed
```

Note that we try to import from `rest_framework` as top-level modules
(like views, exceptions, etc.) to keep the namespace clean.

###### Absolute Imports from lib and conf

```python
from happybudget.lib.utils import ensure_iterable, get_nested_attribute
from happybudget.lib.utils.urls import parse_ids_from_request
```

###### Absolute Imports from app

```python
from happybudget.app.io.fields import Base64ImageField
from happybudget.app.io.serializers import SimpleAttachmentSerializer
from happybudget.app.io.models import Attachment
from happybudget.app.tabling.serializers import row_order_serializer
```

###### Relative Imports

```python
from .models import BaseBudget, Budget
from .permissions import budget_is_first_created
```

Note that we strictly enforce that all relative imports be done only for files
in the same level of the tree. Relative imports from files further up the
directory are not used:

```python
from ..models import BaseBudget, Budget
from ..permissions import budget_is_first_created
```

Putting it all together, we have the following import structure:

```python
import datetime
import os
import time

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, IntegrityError

from rest_framework import views, exceptions, viewsets, serializers, generics
from rest_framework.serializers import as_serializer_error
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from happybudget.lib.utils import ensure_iterable, get_nested_attribute
from happybudget.lib.utils.urls import parse_ids_from_request

from happybudget.app.io.fields import Base64ImageField
from happybudget.app.io.serializers import SimpleAttachmentSerializer
from happybudget.app.io.models import Attachment
from happybudget.app.tabling.serializers import row_order_serializer

from .models import BaseBudget, Budget
from .permissions import budget_is_first_created
```

### Explicit Imports of Internal Modules

Consider we are in a file in the project, `happybudget.app.subaccount.serializers`
for purposes of example. We want to import several serializers from
`happybudget.app.tagging.serializers`. Imports of internal modules & files
should never be done at the higher level module. An example of importing
internal files from a higher level module would be the following:

```python
# happybudget.app.subaccount.serializers
from happybudget.app.tagging import serializers
```

Or even

```python
# happybudget.app.subaccount.serializers
from happybudget.app.tagging import serializers as tagging_serializers
```

The reason we strictly avoid this is the following: Let’s assume that
`happybudget.app.tagging.serializers` contains two serializers, `TagSerializer`
and `ColorSerializer`. Now let’s assume that some other developer decides to
move `TagSerializer` into another file. There are two types of errors that we
may get, depending on whether or not we import and access `TagSerializer` as an
import of it’s higher-level module or an explicit import of the object itself.

#### AttributeError

If we were to access `TagSerializer` from the higher-level module inside of a
scoped execution block after it was moved, we would get an `AttributeError` when
the Python interpreter encounters the line of code where
`tag_serializers.TagSerializer` is accessed:

```python
# happybudget.app.subaccount.serializers
from rest_framework import decorators, status
from happybudget.app.tagging import serializers as tagging_serializers

@decorators.api_view(methods=["GET"])
def my_view(instance):
    # We will not get an error until this line of code is executed.
    data = tagging_serializers.TagSerializer(instance=instance).data
    return response.Response(data, status=status.HTTP_200_OK)
```

This would happen while users are currently using the application.

#### ImportError

On the other hand, if we perform the import as

```python
# happybudget.app.subaccount.serializers
from happybudget.app.tagging.serializers import TagSerializer
```

then the server would not even start due to an `ImportError`, allowing us to
see the error before we deploy the application to a production instance - saving
us from the embarrassment that would come with a large number of users not
being able to access parts of the application.

> There are some exceptions to this rule that we apply consistently throughout
> the application code, but those imports are from files that are very static
> and unlikely to change - which makes less specific imports from it
> more dangerous.

```python
from happybudget.app import signals, views
```

## Linting

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

### Flake8

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

#### No Pragma

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

### Pylint

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

### Ignored Error Codes

#### W503: Line break before a binary operator.

Both W503 and W504 are concerned with where a line break occurs with respect to
a binary operator. While W503 prohibits line breaks before a binary operator,
W504 prohibits line breaks after a binary operator. If both W503 and W504 were
not ignored, then we wouldn’t be able to perform line breaks around binary
operators - which is sometimes useful. However, for consistency, we only disable
W503. This means that line breaks and binary operators should look like the
following:

```python
self.accumulated_markup_contribution = functools.reduce(
    lambda current, sub: current + sub.markup_contribution
    # Line Break Before Binary Operator
    - sub.accumulated_markup_contribution,
    children,
    0
)
```

#### E124: Closing bracket does not match visual indentation.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

#### E128: Continuation line under-indented for visual indent.

Without E128 disabled, the following function would have to be written as
follows (assuming that writing the signature on 1 line exceeds the 80 character
limit):

```python
def test_update_markup_children(api_client, user, budget_f, create_markup,
                                                            models):
```

This is incredibly annoying, as you usually have to indent with both tabs and
spaces to achieve the correct indentation - and Python control flow is based
on the tab (4-space) indent. With E128 disabled, we can write the above signature
as:

```python
def test_update_markup_children(api_client, user, budget_f, create_markup,
  models):
```

##### Indentation Usages in Function Signatures and Calls

The majority of the time - in function signatures - we try to write arguments
on the same line up until the 80 character limit and then continue on the next
line after an indentation (as shown in the above code snippet). In 99% of the
use cases, we try to avoid writing function signatures as the following:

```python
def test_update_markup_children(
  api_client,
  user,
  budget_f,
  create_markup,
  models
):
```

##### Indentation Usages in Function Calls and Class Instantiation

Indentation usage in function calls is a little bit more flexible. The trick
is to balance readability without taking up an enormous amount of space for a
single call or instantiation. As it is harder to come up with concrete definitions
for this style, you can never go wrong looking at the code and trying to stay
consistent with how it is currently written.

###### General Rule of Thumb

The general rule of thumb that can be used to determine how to write the call
or instantiation is as follows:

1. Writing on 1 Line Exceeds 80 Character Limit
  - The number of arguments is greater than or equal to 3.
    - Use one line per argument.
  - The number of arguments is two or less.
    - Write line up to 80 character limit is reached and then indent new line one time for continuation.
  - An argument is a dictionary.
    - Dictionary can be parsed into multiple lines.
2. Writing on 1 Line Does Not Exceed 80 Character Limit
  - The number of arguments is greater than or equal to 3.
    - Acceptable to write one line per argument if the arguments are keyword arguments.
  - The number of arguments is two or less.
    - Always write on a single line.
  - An argument is a dictionary
    - Write on a single line (which should not exceed 80 character limit) unless number of dictionary keys exceeds 2, in which case it is acceptable to write on multiple lines.

Some examples of styles that abide by these guidelines are as follows:

```python
# 80 Character Limit Exceeded or Not Exceeded
previous_field = TablePrimaryKeyRelatedField(
  required=False,
  allow_null=True,
  write_only=True,
  table_filter=self._table_filter
)
```

```python
# 80 Character Limit Not Exceeded
previous_field = TablePrimaryKeyRelatedField(required=False, allow_null=True)
```

```python
# 80 Character Limit Exceeded
self.bulk_update(
  instances,
  tuple(self.model.CALCULATED_FIELDS) + tuple(update_fields),
  mark_budgets=False
)
```

```python
# 80 Character Limit Not Exceeded
self.bulk_update(instances, tuple(...), mark_budgets=False)
```

```python
# 80 Character Limit Not Exceeded
self.create(data={"name": "Jack", "email": "Jack"})
```

```python
# 80 Character Limit Exceeded
self.create("jack@gmail.com", "Jack Johnson", data={
  "company": "Boeing",
  "position": "Engineer"
})
```

```python
# 80 Character Limit Exceeded
self.create(
  "jack@gmail.com",
  "Jack Johnson",
  data={"company": "Boeing", "position": "Engineer"}
)
```

```python
# 80 Character Limit Exceeded or Not Exceeded
self.create(data={
  "name": "Jack",
  "email": "jack@gmail.com",
  "position": "Engineer"
})
```
