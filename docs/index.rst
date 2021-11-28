.. include:: readme.rst

..
    Create a "hidden" table of contents, so that Sphinx doesn't complain about
    documents not being included in any toctree; note that we actually have
    links in the sidebar, however Sphinx doesn't know about this.

    See also: https://stackoverflow.com/a/60491434/10237506

.. toctree::
   :hidden:

   readme
   overview
   installation
   quickstart
   examples
   wiz_cli
   using_field_properties
   python_compatibility
   common_use_cases/index
   advanced_usage/index
   modules
   contributing
   history
