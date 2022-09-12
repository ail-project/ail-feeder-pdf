import os, re
import shutil
import fitz
import exiftool
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
    """Push json to AIL"""
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
    

#############
# Arg Parse #
#############

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
        print("\n\n[-] Error during creation of AIL instance")
        exit(0)

if not args.pdf and not args.file_pdf:
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
    pathToSaveImagePage = os.path.join(pathToSave, 'ImagePages')

    if not os.path.isdir(pathToSave):
        os.mkdir(pathToSave)
    if not os.path.isdir(pathToSaveImagePage):
        os.mkdir(pathToSaveImagePage)

    # open file
    pdf_file = fitz.open(pdf_filename)
    text_file = ""


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

    #################
    # Extract Image #
    #################

    # iterate over PDF pages
    for page_index in range(len(pdf_file)):
        
        # get the page itself
        page = pdf_file[page_index]

        # get text
        text_file += page.get_text('text')
        cp = 0
        
        if page.get_images():
            for image_index, img in enumerate(page.get_images(), start=1):                
                # extract the image bytes
                base_image = pdf_file.extract_image(img[0])
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                with open(os.path.join(pathToSaveImagePage, f"image-{page.number}_{cp}.{image_ext}"), "wb") as write_img:
                    write_img.write(image_bytes)
                cp += 1

    # Check if pdf contains characters
    x = re.match(r"\S", text_file, flags=re.MULTILINE)
    if x:
        data = text_file
    else:
        data = 'null'


    ################
    # Extract meta #
    #  From image  #
    ################

    for img in os.listdir(pathToSaveImagePage):
        locPath = os.path.join(pathToSaveImagePage, img)
        if not os.path.isdir(locPath):
            with exiftool.ExifTool() as et:
                img_metadata = et.get_metadata(locPath)
                img_name = img.split(".")[0]
                meta[f"pdf_feeder:{img_name}"] = img_metadata

            # Openstreetmap url generation
            if "EXIF:GPSLatitude" in img_metadata.keys():
                lat = img_metadata["EXIF:GPSLatitude"]
                lon = img_metadata["EXIF:GPSLongitude"]
                meta[f"pdf_feeder:{img_name}"]["openstreetmap"] = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=12"

    pushToAIl(data, meta)

    try:
        shutil.rmtree(pathToSave)
    except:
        pass
