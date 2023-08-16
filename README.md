# ail-feeder-pdf
This AIL feeder is a generic software to extract informations from PDF and feed AIL via AIL ReST API.



## Requirements

- [PyMuPDF](https://github.com/pymupdf/PyMuPDF)
- [PyExifTool==0.4.13](https://github.com/smarnach/pyexiftool)
- [pyail](https://github.com/ail-project/PyAIL)



## Usage

~~~bash
dacru@dacru:~/git/ail-feeder-pdf/bin$ python3 feeder-pdf.py --help  
usage: feeder-pdf.py [-h] [-p PDF [PDF ...]] [-fp FILE_PDF] [-d] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -p PDF [PDF ...], --pdf PDF [PDF ...]
                        list of pdf to analyse
  -fp FILE_PDF, --file_pdf FILE_PDF
                        file containing list of pdf
  -d, --debug           debug mode
  -v, --verbose         display more info
  
~~~



## JSON output format to AIL

- `source` is the name of the AIL feeder module
- `source-uuid` is the UUID of the feeder (unique per feeder)
- `data` is text found in pdf
- `meta` is the generic field where feeder can add the metadata collected

Using the AIL API, `data` will be compress in gzip format and encode with base64 procedure. Then a new field will created, `data-sha256` who will be the result of sha256 on data after treatment.



## Output

~~~json
{'data': "",
 'meta': {'pdf_feeder:ExifTool:ExifToolVersion': 12.43,
          'pdf_feeder:File:Directory': '.',
          ..., // Exif metadata
          
          'pdf_feeder:image-0_0': {'Composite:ImageSize': '2078 1559',
                                   'Composite:Megapixels': 3.239602,
                                   'ExifTool:ExifToolVersion': 12.43,
                                   'File:BitsPerSample': 8,
                                   'File:ColorComponents': 3,
                                   ... // Exif metadata of image
         						  }
		}
}

~~~



`pdf_feeder:image-x_y`: 

- x: page of the document where the image is found.
- y: numbers of images found in a specific page. start at 0.


## License


This software is licensed under [GNU Affero General Public License version 3](http://www.gnu.org/licenses/agpl-3.0.html)

Copyright (C) 2022-2023 CIRCL - Computer Incident Response Center Luxembourg

Copyright (C) 2022-2023 David Cruciani

Copyright (C) 2023 Aurelien Thirion

