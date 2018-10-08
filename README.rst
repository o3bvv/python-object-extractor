Python Object Extractor
=======================

Extract Python object (like class, function, etc) with its dependencies from
local project.


Deliverables
------------

Package provides executable ``python-object-extractor``.


Synopsis:

.. code-block::

  usage: python-object-extractor [-h] [-p PROJECT_PATH] [-m OUTPUT_MODULE_PATH]
                                 [-r OUTPUT_REQUIREMENTS_PATH]
                                 [-n OUTPUT_OBJECT_NAME]
                                 object_reference

  Extract Python object with its dependencies from local project.

  positional arguments:
    object_reference      reference to object to extract. Example:
                          'importable.module:object'

  optional arguments:
    -h, --help            show this help message and exit
    -p PROJECT_PATH, --project_path PROJECT_PATH
                          path to local project directory (default: .)
    -m OUTPUT_MODULE_PATH, --output_module_path OUTPUT_MODULE_PATH
                          path to output Python module containing extracted
                          object, for example, 'main.py'. Use '-' to output to
                          STDOUT (default: -)
    -r OUTPUT_REQUIREMENTS_PATH, --output_requirements_path OUTPUT_REQUIREMENTS_PATH
                          path to output requirements file, for example,
                          'requirements.txt'. Use '-' to output to STDOUT
                          (default: -)
    -n OUTPUT_OBJECT_NAME, --output_object_name OUTPUT_OBJECT_NAME
                          output name of target reference. By default it's taken
                          from 'object_reference'. For example, output object
                          name will be 'object' for object reference
                          'importable.module:object' (default: None)


Usage examples
--------------

Extract function from package located in current directory and print to
``STDOUT``:

.. code-block:: bash

  python-object-extractor package.module:function


Extract function from package located in current directory, name it as ``main``
and print results to ``STDOUT``:

.. code-block:: bash

  python-object-extractor package.module:function -n main


Extract function from package located in a given directory and print to
``STDOUT``:

.. code-block:: bash

  python-object-extractor package.module:function -p /path/to/project


Extract function from package located in a given directory and save results to
files ``main.py`` and ``requirements.txt``:


.. code-block:: bash

  python-object-extractor package.module:function -p /path/to/project -m ./main.py -r ./requirements.txt
