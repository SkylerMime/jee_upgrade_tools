# File Reformatter

Simple script to reformat common problems in legacy JSF codebases

Java:
- Replaces depreacted ObjectUtils.toString(obj) with Objects.toString(obj, "")

Xhtml:
- Replaces ui-g elements with PrimeFlex p-grid elements

To run on a file:
```bash
python reformat_file.py [file_path]
```

To run the test suite:

```bash
pip install pytest
pytest .
```
