# Tibetan Text Scripts
Various scripts manipulating Tibetan Texts, including scripts to:

1. Convert Word Files in Sambhota fonts to Unicode (Windows and Mac)
2. Insert milestones in Sambhota converted files based on OCR
2. Add THL Styles to a Word Doc with options to apply styles to annotations and/or milestons
3. Convert between txt, rtf, and docx files (on Mac)
4. Split a volume into texts

This was developed originally as Sambhota Conversion Scripts for the Peltsek Kama files that were in Sambhota font, but 
in the process of developing another set of scripts InsertMilestones in the repo by the same name at 
https://github.com/thl-texts/insert-milestones.git, it was decided to merge those scripts here and create a general 
Tibetan Text Scripts repo.

* **Developer:** Than Grove
* **Creation Date:** July 31, 2019

## Installation 
As detailed in the next section, the Sambhota conversion method uses both a Mac OS 10 and Windows 10 environment. The main 
conversion script is a Python script run on the Mac. It was written for Python 3 and only uses two additional packages:

* lxml
* python-doc

A `requirements.txt` file has been included so one can set up a virtual environment. This is done through the following 
steps:

1. Install Python on your Mac using Homebrew with `brew install python3` (Note: if you don't have Homebrew 
installed, look to [its installation page](https://docs.brew.sh/Installation)). This will also install `pip`
2. In a terminal window navigate into this repos directory on your Mac machine
3. Type `python -m virtualenv venv`
4. Type `source venv/bin/activate`
5. Type `pip install -r requirements.txt`

*Note:* To get out of the virtual environment, either close the terminal or type `deactivate`

## Inserting Milestones into Chunked Texts Based on OCR (Kama)

This is the process to take chunked texts of a Kama volume and insert the milestones. 
1. Copy volume chunked files into the workspace\in folder
2. Run `insert_milestones.py -v 96 -s 8` where `-v` is the volume number and `-s` is the page that the volume starts on, 
skipping introductory TOC etc., i.e., the first page of first text.
3. Run `add_styles2docx.py -i workspace/out -a -m` 

Other options include:
* `-b` (blank pages skipped in scan so scan image number doesn't count them), 
* `-br` (pages which represent a new file to force a break when script not working properly),
* `-c` Clear files from in and out folders and copy in new raw chunk files for the volume in question, 
* `-d` turn on debugging.

## Overall Process for Conversion of Sambhota Files

The conversion process is a multi-stepped process that requires both a Mac and a Windows machine to proceed 
most efficiently. I did it by using Virtual Box to create a virtual Windows 10 machine on my Mac and shared 
the files between the virtual Windows machine and my Mac through UVA Box, but other ways to transfer files 
are also possible. When you just want to convert the individual files into templated Word docs with the same 
name, then the steps in the process are:

1. Download the original Word .doc files to the `in` folder here on Mac
2. Run `doc2rtf.sh in out` - this converts the .doc files to .rtf and puts in the `out` folder
3. Transfer to Windows machine (Upload to UVA Box and then download to Windows Virtual machine), putting them 
in the `in` folder
4. Run the batch script `convertSamRTF.bat`. This will use UDP to convert the Sambhota files to Unicode 
and will put the converted Unicode files in the `out` folder
    * Make sure that in UDP Advance settings you click the box "Put smaller font between « and »"
5. Transfer the unicode RTF files to the `in` folder on the Mac machine
6. Run the `rtf2docx.sh in out` script, which converts the files to `.docx` format and puts them in the `out` folder. 
Put the `.docx` files in the `in` folder.
7. Run the python script `add_styles2docx.py`. This will convert all documents in the `in` folder and put them in the 
`out` folder

The converted `.docx` files will then be in the `out` folder

The Python script will convert each document into Unicode .docx file with all paragraphs as Paragraph style 
but with the text between the « and » marked up as Annotations style. A metadata table will be placed at the top 
of the document.

The document template used is in the `resources` folder. It is `tibtext-styled-tpl.docx`.

## Adding THL Styles to Texts
The script add_styles2docx.py will take all the .docx files in the /in folder and add the THL styles to them, producing 
new documents in the out folder. When this script is run, it gives you three options. You can choose 1. whether or not 
to add the metadata table and basic headers to the resulting Word doc (this is primarily for individual texts not volumes), 
2. whether or not to convert text surrounded by << and >> into annotations by removing those markers and applying the 
Word style, and 3. whether or not to apply the styles to the page and line milestones in the doc with the format 
"[23.4]".

## Spliting into Texts
Sometimes the Sambhota texts received are volumes or volume "chunks" that need to be broken up into individual texts. 
For the Kama I wrote a script that did this, which may work for other collections. This script is `split_into_texts.py`
All documents to be processed should be put in the `in` folder and the results will go in the `out` folder. There are 
two global variables of note. `filefilterstr` is the file name prefix for the files to process in the IN folder, 
assuming they all begin with the same string such as "KAMA". `text_break_string` is the string used to split the chunks
into texts. This is the universal string that separates two texts in a document. For the KAMA it was '༄༅'. Further 
modifications will need to be done to break on the 'བཞུགས་སོ།' since the line just before will also need to be included in 
the subsequent text. This has not yet been implemented. (Update: This method is problematic creating too many false breaks 
and/or missing real breaks. Better to change or add a script to break up based on cataloging data once the milestones 
have been inserted.)

**NOTE**: It is _important_ that the styles be up-to-date. Download the latest Word doc template with THL Styles
from [this Google Docs link](https://drive.google.com/open?id=1e5BL8fZym-YnbQTyN-qpWDu5nbqqn98i) (It is in the folder
Toolbox for Tibetan Library > Tibetan Text Work > 
[Inputting & Editing Tibetan Texts](https://drive.google.com/open?id=1ey66coelDLu-Mo2YcZIxfyy1kX0a1xGX)). Then open a new 
document with that template, paste in the metadata table from the old one, and replace the old one at `resources\tibtext-styled-tpl.docx`

**Comments**: 
* Some scripts such as `rtf2txt.sh` are residual from previous attempts. They are not used in the conversion but I have 
left them in the repo in case they are useful in the future.
