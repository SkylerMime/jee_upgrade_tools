# File Reformatter

Simple script to reformat common problems in legacy Java codebases

- Replaces depreacted ObjectUtils.toString(obj) with Objects.toString(obj, "")

To run the test suite:

```bash
pip install pytest
pytest .
```
