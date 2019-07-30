# Sambhota Conversion Scripts
Various scripts for Windows 10 and Mac OS X to convert files with Sambhota fonts to Unicode Tibetan.

This was developed originally for the Peltsek Kama files that were in Sambhota font.

## Overall Process

The conversion process is a multi-stepped process that requires both a Mac and a Windows machine to proceed 
most efficiently. I did it by using Virtual Box to create a virtual Windows 10 machine on my Mac and shared 
the files between the virtual Windows machine and my Mac through UVA Box, but other ways to transfer files 
are also possible. The steps in the process were:

1. Download the original Word .doc files to the `in` folder here on Mac
2. Run `doc2rtf.sh in out` - this converts the .doc files to .rtf and puts in the `out` folder
3. Transfer to Windows machine (Upload to UVA Box and then download to Windows Virtual machine), putting them 
in the `in` folder
4. Run the batch script `convertSamRTF.bat`. This will use UDP to convert the Sambhota files to Unicode 
and will put the converted Unicode files in the `out` folder
    * Make sure that in UDP Advance settings you click the box "Put smaller font between « and »"
5. Transfer the unicode RTF files to the `in` folder on the Mac machine
6. Run the `rtf2docx.sh` script, which converts the files to `.docx` format and puts them in the `out` folder. 
Put the `.docx` files in the `in` folder.
7. Run the python script `add_styles2docx.py`

The converted `.docx` files will then be in the `out` folder

The Python script will convert each document into Unicode .docx file with all paragraphs as Paragraph style 
but with the text between the « and » marked up as Annotations style. A metadata table will be placed at the top 
of the document.

The document template used is in the `resources` folder. It is `tibtext-styled-tpl.docx`.

**NOTE**: It is _important_ that the styles be up-to-date. Download the latest Word doc template with THL Styles
from [this Google Docs link](https://drive.google.com/open?id=1e5BL8fZym-YnbQTyN-qpWDu5nbqqn98i) (It is in the folder
Toolbox for Tibetan Library > Tibetan Text Work > 
[Inputting & Editing Tibetan Texts](https://drive.google.com/open?id=1ey66coelDLu-Mo2YcZIxfyy1kX0a1xGX)). Then open a new 
document with that template, paste in the metadata table from the old one, and replace the old one at `resources\tibtext-styled-tpl.docx`
