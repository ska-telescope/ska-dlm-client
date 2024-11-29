The file invalid-ska-data-product.yaml only differs from the "good" version by the
addition of ```_id``` to the execution_block key. It only needs to be enough of a change
to trigger the code to return a ```None```.

```sh
$ diff ska-data-product.yaml invalid-ska-data-product.yaml
3c3
< execution_block: eb-m001-20191031-12345
---
> execution_block_id: eb-m001-20191031-12345
```

There is no specific meaning to ending the test data product files in ```.ext```. The
files are never read as "meaningful data".
