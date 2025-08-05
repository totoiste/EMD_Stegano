# EMD_Stegano
<p align="left">
    A python script to manage images steganography Embedding by Exploiting Modification Direction.<br>
    This is an implementation of "Efficient Steganographic Embedding by Exploiting Modification Direction"<br>
    <a href="https://staff.emu.edu.tr/alexanderchefranov/Documents/CMSE492/ZhangIEEECL2006.pdf">IEEE COMMUNICATIONS LETTERS, VOL. 10, NO. 11, NOVEMBER 2006</a><br>
    Xinpeng Zhang and Shuozhong Wang
</p>

## Features

 - [x] Give info about capacity to hide data in an image.
 - [x] Hide a secret message or file content in an image.
 - [x] Extract data embedded with this efficient and specific method in an image.
 - [x] Search for information that may have been hidden by this process 
 - [x] Save output in a file or in a specified image
 - [x] Supports all PIL images types
 - [x]  Manage only grayscale image, if not convert !

## Usage

```python
$ python3 EMD_stegano.py -h
  ______ __  __ _____     _____ _
 |  ____|  \/  |  __ \   / ____| |
 | |__  | \  / | |  | | | (___ | |_ ___  __ _  __ _ _ __   ___
 |  __| | |\/| | |  | |  \___ \| __/ _ \/ _` |/ _` | '_ \ / _ \           v1.1
 | |____| |  | | |__| |  ____) | ||  __/ (_| | (_| | | | | (_) |
 |______|_|  |_|_____/  |_____/ \__\___|\__, |\__,_|_| |_|\___/           @totoiste
                                         __/ |
                                        |___/
  -----Efficient Steganographic Embedding by Exploiting Modification Direction-----

usage: EMD_stegano.py [-h] [-v] {hide,extract,info,search} ...

The EMD_Stegano script allows you to hide DATA in an image or read hidden DATA from an image with a Steganographic process called EMD (Exploiting Modification Direction)

positional arguments:
  {hide,extract,info,search}
                        choose an action
    hide                Hide data in image
    extract             Extract data from image
    info                Return info about image capacity
    search              search text hidden into image

options:
  -h, --help            show this help message and exit
  -v, --debug           Debug mode.
```

## Demonstration

Example to hide Secret Message in image.png
```python
$ python3 EMD_stegano.py hide -n 11 -in image.png -it "S3cr3t Text hidden in Image" -out image_EMD.png
```
Example to extract Secret Message from image_EMD.png
```python
$ python3 EMD_stegano.py -v extract -n 11 -in image_EMD.png -l 27
```
Example to search Secret Message in image_EMD.png
```python
$ python3 EMD_stegano.py -v search -l 27 -in image_EMD.png
```
## Contributors

Pull requests are welcome. Feel free to open an issue if you want to add other features.
