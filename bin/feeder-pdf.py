import os, re
import shutil
import fitz
import pdfx
import exiftool
import pprint
from PIL import Image
import argparse
import configparser
from pyail import PyAIL

dir_path = os.path.dirname(os.path.realpath(__file__))
uuid = "19055d23-da04-46e8-9dbc-6f71c23a47da"

## Config
pathConf = '../etc/ail-feeder-pdf.cfg'

if os.path.isfile(pathConf):
    config = configparser.ConfigParser()
    config.read(pathConf)
else:
    print("[-] No conf file found")
    exit(-1)

if 'general' in config:
    uuid = config['general']['uuid']

if 'ail' in config:
    ail_url = config['ail']['url']
    ail_key = config['ail']['apikey']


def pushToAIl(data, meta):
    default_encoding = 'UTF-8'

    json_pdf = dict()
    json_pdf['data'] = data
    json_pdf['meta'] = meta

    source = 'pdf-feeder'
    source_uuid = uuid

    if debug:
        print(json_pdf)
    else:
        pyail.feed_json_item(data, meta, source, source_uuid, default_encoding)
    

parser = argparse.ArgumentParser()
parser.add_argument('-p', "--pdf", nargs='+', help="list of pdf to analyse")
parser.add_argument('-fp', "--file_pdf", help="file containing list of pdf")
parser.add_argument("-d", "--debug", help="debug mode", action="store_true")
parser.add_argument("-v", "--verbose", help="display more info", action="store_true")
args = parser.parse_args()

debug = args.debug
verbose = args.verbose

## Ail
if not debug:
    try:
        pyail = PyAIL(ail_url, ail_key, ssl=False)
    except Exception as e:
        # print(e)
        print("\n\n[-] Error during creation of AIL instance")
        exit(0)

if not args.pdf and args.file_pdf:
    print("Error passing pdf")
    exit(0)
elif args.pdf:
    pdf_list = args.pdf
elif args.file_pdf:
    with open(args.file_pdf, 'r') as read_file:
        pdf_list = read_file.readlines()

for pdf_filename in pdf_list:
    if verbose:
        print(f"\n{pdf_filename}")
    pathToSave = os.path.join(dir_path, pdf_filename.split('.')[0])
    pathToSaveDotYellow = os.path.join(pathToSave, 'outDotYellow')
    pathToSaveImagePage = os.path.join(pathToSave, 'ImagePages')

    if not os.path.isdir(pathToSave):
        os.mkdir(pathToSave)
    if not os.path.isdir(pathToSaveDotYellow):
        os.mkdir(pathToSaveDotYellow)
    if not os.path.isdir(pathToSaveImagePage):
        os.mkdir(pathToSaveImagePage)


    ###############
    # Yellow Dots #
    ###############

    # doc = fitz.open(pdf_filename)  # open document

    # for page in doc:  # iterate through the pages
    #     pix = page.get_pixmap()  # render page to an image
    #     out = os.path.join(pathToSave, "page-%i.png" % page.number)
    #     pix.save(out)  # store image as a PNG

    # for file in os.listdir(pathToSave):
    #     fimg = os.path.join(pathToSave, file)
    #     if not os.path.isdir(fimg):
    #         blue = Image.open(fimg).split()[2]

    #         yellow_dot = os.path.join(pathToSaveDotYellow, file)
    #         blue.point(lambda x: (256-x)**2).save(f"{yellow_dot}")

    #####################
    # Extract Reference #
    #    Url  &  Text   #
    #####################

    if verbose:
        print("[+] Extract Reference, Url & Text")

    pdf = pdfx.PDFx(pdf_filename)
    references_dict = pdf.get_references_as_dict()
    text_file = pdf.get_text()

    # Check if pdf contains characters
    x = re.match(r"\S", text_file, flags=re.MULTILINE)
    if x:
        data = text_file
    else:
        data = 'null'

    # print(references_dict)

    ####################
    # Extract Metadata #
    ####################

    if verbose:
        print("[+] Extract Metadata")

    with exiftool.ExifTool() as et:
        metadata = et.get_metadata(pdf_filename)

    meta = dict()
    for key in metadata.keys():
        meta[f"pdf_feeder:{key}"] = metadata[key]

    meta['pdf_feeder:reference'] = dict()
    if references_dict:
        meta['pdf_feeder:reference']['url'] = references_dict['url']
        meta['pdf_feeder:reference']['pdf'] = references_dict['pdf']
    else:
        meta['pdf_feeder:reference']['url'] = []
        meta['pdf_feeder:reference']['pdf'] = []

    pprint.pprint(meta)
    # exit(0)

    #################
    # Extract Image #
    #################

    # open the file
    pdf_file = fitz.open(pdf_filename)
    
    # iterate over PDF pages
    for page_index in range(len(pdf_file)):
        
        # get the page itself
        page = pdf_file[page_index]
        image_list = page.get_images()
        cp = 0
        
        # printing number of images found in this page
        if image_list:
            # print(f"[+] Found a total of {len(image_list)} images in page {page_index}")
        
            for image_index, img in enumerate(page.get_images(), start=1):
                
                # get the XREF of the image
                xref = img[0]
                
                # extract the image bytes
                base_image = pdf_file.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                with open(os.path.join(pathToSaveImagePage, f"page-{page.number}_{cp}.{image_ext}"), "wb") as write_img:
                    write_img.write(image_bytes)

    pushToAIl(data, metadata)

    # try:
    #     shutil.rmtree(pathToSaveImagePage)
    # except:
    #     pass
    
    try:
        shutil.rmtree(pathToSaveDotYellow)
    except:
        pass
