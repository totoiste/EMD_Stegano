#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : EMD_Stegano.py
# Author             : totoiste (@T0to1st3)
# Date created       : 13/07/2025
# V2.1

from PIL import Image
import argparse
import math
import sys
import os

"""
Implementation of "Efficient Steganographic Embedding by Exploiting Modification Direction"
IEEE COMMUNICATIONS LETTERS, VOL. 10, NO. 11, NOVEMBER 2006
Xinpeng Zhang and Shuozhong Wang
https://staff.emu.edu.tr/alexanderchefranov/Documents/CMSE492/ZhangIEEECL2006.pdf
https://www.researchgate.net/publication/3417888_Efficient_Steganographic_Embedding_by_Exploiting_Modification_Direction

Manage only grayscale image, if not convert it!
"""

"""
Class IMAGE 
-----------
    - Object = Pillow Image
    - Pixels have coordinates (x,y)
        - x is relative to the width axis 
        - y is relative to the height axis 
    - get_coord_xy is a function which returns coordinates x,y for a digit defined.
        digits are numbers in (2n+1)-ary notational system defined in EMD class 
        digits are calculated in EMD by f function
    - digit_index is the index in digits which are the conversion of SECRET to be hidden in numbers
        As a digit is coded in n pixels, the n-th digit position could be calculated -> get_coord_xy()
    - stego_group is a group of n pixels hiding one bit of SECRET

"""
class IMAGE:
    def __init__(self, image_path: str) -> None:
        try:
            img = Image.open(image_path)
        except Exception:
            print(f"\x1b[1;91m❌\x1b[0m \x1b[96mNot an image file !\x1b[0m")
        self.img = img
        self.mode = img.mode
        self.pixels = img.load()
        self.width, self.height = img.size

    # Extract and calculate digits from IMAGE 
    def get_digits(self, n: int, length: int) -> list:
        base = 2 * n + 1
        bits_per_digit = math.floor(math.log2(base))

        digits = []
        nb_digits = math.ceil(length * BYTE_LENGTH / bits_per_digit)
        for index in range(nb_digits):
            Sg = STEGO_GROUP(self,index,n)
            digits.append(Sg.get_digit())
            if options.verbose:
                print(f"\x1b[1m[\x1b[93m++\x1b[0m\x1b[1m]\x1b[0m For Stego group {index} : p = {Sg.pixels} and f(p) = {Sg.get_digit().value} \x1b[0m")
        if options.debug or options.verbose:
            print(f"\x1b[1m[\x1b[93m+\x1b[0m\x1b[1m]\x1b[0m Get {len(Sg.pixels)} digits from image\x1b[0m")
        return digits

    def convert_grayscale(self) -> None:
        self.img = self.img.convert("L")
        
    def get_nb_pixels(self) -> int:
        return self.width*self.height

    def set_pixel(self, x: int, y: int, value: int) -> None:
        self.pixels[x, y] = value

    def save(self, image_output_path: str) -> None:
        self.img.save(image_output_path)

    def get_xy(self, index: int, n: int) -> list:
        line = self.width // n
        y = index // line 
        x = (index % line) * n
        return x, y

"""
Class DIGIT
-----------
    - Dgit is a number in base (2n + 1)
    - One digit contains bits_per_digit (= math.floor(math.log2(base))) bits
"""
class DIGIT:
    def __init__(self, n: int, value: int) -> None:
        self.n = n
        self.base = 2 * n + 1
        self.bits_per_digit = math.floor(math.log2(self.base))
        self.value = value
    
    def convert_to_bits(self):
        return bin(self.value)[2:].zfill(int(self.bits_per_digit))

"""
Class STEGO_GROUP
-----------
    - stego_group is a group of n pixels of IMAGE hiding one digit of SECRET
    - one digit is a number in base (2n + 1)
    - one digit contains bits_per_digit (= math.floor(math.log2(base))) bits

"""
class STEGO_GROUP:
    def __init__(self, image: IMAGE, index: int, size: int) -> None:
        self.index = index
        self.image = image
        self.n = size
        self.base = 2 * self.n + 1
        self.x, self.y = self.image.get_xy(self.index, self.n)
        self.pixels = self.get_pixels()

    def get_pixels(self) -> list:
        p = [self.image.pixels[self.x + i, self.y] for i in range(self.n)]
        return p

    def set_pixels(self, new_values: list) -> None:
        try:
            for i in range(self.n):
                self.image.set_pixel(self.x + i, self.y, new_values[i])
        except Exception as e:
            print(f"\x1b[1;91m❌\x1b[0m \x1b[96mChange pixel values error -> {type(e)} : {e}\x1b[0m")

    # Calulation of f as a weighted sum modulo (2n + 1) 
    # f(g1, g2,...,gn) = SUM[(gi*i)] mod (2n + 1) for i = 1..n
    def get_digit(self) -> DIGIT:
        weighted_sum = 0
        for i in range(self.n):
            weighted_sum += (i + 1) * self.pixels[i]
        Digit = DIGIT(self.n, weighted_sum % self.base)
        return Digit

"""
Class SECRET
-----------
    - This class is usefull to manage SECRET to hide in IMAGE or to manage SECRET
      extracted from IMAGE
    - data can be a string, byte or array of bits
"""
class SECRET:
    def __init__(self, data, n) -> None:
        self.length = len(data)
        self.n = n
        self.base = 2 * self.n + 1
        self.bits_per_digit = math.floor(math.log2(self.base))

        #Manage format inputs
        if isinstance(data, str): 
            self.bytes = data.encode('utf-8')
        elif all(isinstance(x, int) and x in (0, 1) for x in data): #Array of bits
            self.bytes = []
            for i in range(0, len(data), BYTE_LENGTH):
                byte = data[ i : i + BYTE_LENGTH]
                self.bytes.append(int(''.join(str(bit) for bit in byte), 2))
            self.bytes = bytes(self.bytes)
        else:
            self.bytes = data

        self.bits = self.bytes_to_bits()

    def bytes_to_bits(self) -> list:
        bit_list = []
        for char in self.bytes:
            bit_list.extend([int(b) for b in bin(char)[2:].zfill(BYTE_LENGTH)])
        return bit_list

    def bits_to_bytes(self, bit_list: list) -> bytes:
        num_bytes = len(bit_list) // BYTE_LENGTH
        byte_values = []
        for i in range(num_bytes):
            byte_bits = bit_list[i*BYTE_LENGTH : (i+1)*BYTE_LENGTH]
            binary_string = "".join(str(b) for b in byte_bits)
            decimal_value = int(binary_string, 2)
            byte_values.append(decimal_value)
        return bytes(byte_values)

    #Convert bits to digits in a (2n + 1)-ary notational system
    def get_digits(self, n: int) -> list:
        digits = []
        for i in range(0, len(self.bits), self.bits_per_digit):
            group = self.bits[i : i + self.bits_per_digit]

            # Manage the case : Secret bits number is not exactly the number of digits * self.bits_per_digit
            if len(group) < self.bits_per_digit:
                group.extend([0] * (self.bits_per_digit - len(group)))

            value = int(''.join(map(str, group)),2) 
            if options.verbose:
                print(f"\x1b[1m[\x1b[93m++\x1b[0m\x1b[1m]\x1b[0m For group of bits {group} in Secret bitstream, digit is {value}\x1b[0m")
            Digit = DIGIT(n, value)
            digits.append(Digit)
        if options.debug or options.verbose:
            print(f"\x1b[1m[\x1b[93m+\x1b[0m\x1b[1m]\x1b[0m Convert {len(digits)} digits from Secret bitstream of length {len(self.bits)}\x1b[0m")
        return digits

    def find_printable_substring(self, length: int, tolerance = 0.90) -> list: 
        for b in range(BYTE_LENGTH):
            raw_bytes = self.bits_to_bytes(self.bits[b:])
            for i in range(len(raw_bytes) - length + 1):
                substring_bytes = raw_bytes[i:i + length]
                decoded_substring = substring_bytes.decode('utf-8', errors='ignore')
                printable_count = sum(1 for char in decoded_substring if char.isprintable())
                if (printable_count / length) >= tolerance:
                    return (substring_bytes,i,b)
        return None

    def __str__(self) -> str:
        return f"{self.bytes}"

"""
Class EMD
-----------
    - The main idea of the proposed steganographic method is that each secret
      digit in a (2n + 1)-ary notational system is carried by n cover pixels,
      where n is a system parameter, and, at most, only one pixel is increased
      or decreased by 1. Actually, for each group of n pixels, there are 2n
      possible ways of modification. The 2n different ways of alteration plus
      the case in which no pixel is changed form (2n + 1) different values of
      a secret digit.
    - Before data-embedding, a data-hider can conveniently convert a secret
      message into a sequence of digits in the notational system with an odd
      base (2n + 1)
    - The base is the (2n + 1)-ary notational system
    - A digit is a number in base 2n + 1
    - A stego group is a group of n pixels including some digits
"""
class EMD:
    def __init__(self, n: int) -> None:
        self.n = n
        self.base = 2 * n + 1
        self.bits_per_digit = math.floor(math.log2(self.base))
        if options.debug or options.verbose:
            print(f"\x1b[1m[\x1b[93m+\x1b[0m\x1b[1m]\x1b[0m n = {self.n}, base (2n+1) = {self.base}, bits per digit = {self.bits_per_digit}\x1b[0m")


    #Modify the correct pixel by incrementing or decrementing of 1 
    #Manage the cases of pixel values = 0 or 255
    def embed(self, Sg: STEGO_GROUP, secret_digit: DIGIT) -> STEGO_GROUP:
        if options.verbose:
            print(f"\x1b[1m[\x1b[93m++\x1b[0m\x1b[1m]\x1b[0m For stego group number {Sg.index:4d} list of pixels = = = = = = = = = = = = = = = = = = = = {Sg.pixels} -> f = {Sg.get_digit().value:4d}\x1b[0m")

        new_Sg = Sg

        if new_Sg.get_digit().value != secret_digit.value:
            s = (secret_digit.value - new_Sg.get_digit().value) % self.base
            if s <= self.n:
                pos = s - 1 
                pixel_to_change = new_Sg.pixels[pos]
                if pixel_to_change == 255:
                    new_Sg.pixels[pos] -= 1
                    new_Sg = self.embed(new_Sg, secret_digit)
                else:
                    new_Sg.pixels[pos] = pixel_to_change + 1
            elif s > self.n:
                pos = self.base - s - 1
                pixel_to_change = new_Sg.pixels[pos]
                if pixel_to_change == 0:
                    new_Sg.pixels[pos] += 1
                    new_Sg = self.embed(new_Sg, secret_digit)
                else:
                    new_Sg.pixels[pos] = pixel_to_change - 1
            if options.verbose:
                print(f"\x1b[1m[\x1b[93m++\x1b[0m\x1b[1m]\x1b[0m    s = {s:6d} so digit {new_Sg.index:4d} changed and to embed secret digit {secret_digit.value:4d} now is equal to {new_Sg.pixels} -> f = {new_Sg.get_digit().value:4d}\x1b[0m")
        else:
            if options.verbose:
                print(f"\x1b[1m[\x1b[93m++\x1b[0m\x1b[1m]\x1b[0m    s = 0      so digit {new_Sg.index:4d} do not change\x1b[0m")

        return new_Sg

    # Hide each byte of data in image
    def hide(self, Secret: SECRET, Img: IMAGE) -> IMAGE:
        if options.debug or options.verbose:
            print(f"\x1b[1m[\x1b[93m+\x1b[0m\x1b[1m]\x1b[0m Secret to hide : {len(Secret.bytes)} bytes and {len(Secret.bits)} bits\x1b[0m")
        if options.verbose:
            print(f"\x1b[1m[\x1b[93m++\x1b[0m\x1b[1m]\x1b[0m Secret bytes to hide is {Secret.bytes}\x1b[0m")
            print(f"\x1b[1m[\x1b[93m++\x1b[0m\x1b[1m]\x1b[0m Secret bits to hide is {Secret.bits}\x1b[0m")
            
        required_digits = math.ceil(len(Secret.bits) / self.bits_per_digit)
        if options.debug or options.verbose:
            print(f"\x1b[1m[\x1b[93m+\x1b[0m\x1b[1m]\x1b[0m Required digits (stego_group) to hide Secret : {required_digits}\x1b[0m")

        if Img.width * Img.height < required_digits * self.n:
            raise ValueError(f"\x1b[1;91m❌\x1b[0mImage too small : {Img.width * Img.height} pixels available, {required_digits * n} required !\x1b[0m")

        Secret_digits = Secret.get_digits(self.n)
        if options.verbose:
            print(f"\x1b[1m[\x1b[93m++\x1b[0m\x1b[1m]\x1b[0m List of {len(Secret_digits)} digits {self.base}-ary to hide are : {[digit.value for digit in Secret_digits]}\x1b[0m")

        for index in range(len(Secret_digits)):
            Sg = STEGO_GROUP(Img, index, self.n)
            new_Sg = self.embed(Sg, Secret_digits[index])
            Sg.set_pixels(new_Sg.pixels)

        print(f"\x1b[1;92m✅\x1b[0m \x1b[96mSecret of {Secret.length} bytes hidden with {len(Secret_digits)} digits of base {self.base} and {len(Secret.bits)} bits\x1b[0m")
        return Img

    def extract(self, Img: IMAGE, data_length: int) -> bytes:
        Img_digits = Img.get_digits(self.n, data_length)

        bits = []
        for digit in Img_digits:
            binary = digit.convert_to_bits()
            bits.extend([int(b) for b in binary])
            if options.verbose:
                print(f"\x1b[1m[\x1b[93m++\x1b[0m\x1b[1m]\x1b[0m  Converting digit = {digit.value:4d} to bits = {binary}\x1b[0m")
        #Keep the exact quantity of bits...
        bits = bits[:data_length * BYTE_LENGTH]

        if options.debug or options.verbose:
            print(f"\x1b[1m[\x1b[93m+\x1b[0m\x1b[1m]\x1b[0m Converted {len(bits)} bits from {len(Img_digits)} digits\x1b[0m")

        if options.verbose:
            print(f"\x1b[1m[\x1b[93m++\x1b[0m\x1b[1m]\x1b[0m numbers {self.base}-ary extracted : {[digit.value for digit in Img_digits]}\x1b[0m")
            print(f"\x1b[1m[\x1b[93m++\x1b[0m\x1b[1m]\x1b[0m Extracted Message in {len(bits)} bits\x1b[0m")
            print(f"\x1b[1m[\x1b[93m++\x1b[0m\x1b[1m]\x1b[0m bits of Secret = {bits}\x1b[0m")
        Secret = SECRET(bits, self.n)

        if options.debug or options.verbose:
            print(f"\x1b[1m[\x1b[93m+\x1b[0m\x1b[1m]\x1b[0m Extracted {Secret.length // BYTE_LENGTH} bytes from image\x1b[0m")
        return Secret

def parseArgs() -> dict:
    parser = argparse.ArgumentParser(add_help=True, description="The EMD_Stegano script allows you to hide SECRET in an image or read hidden SECRET from an image with a Steganographic process called EMD (Exploiting Modification Direction)")
    parser.add_argument("-v", "--debug", action="store_true", default=False, help="Debug mode.")
    parser.add_argument("-vv", "--verbose", action="store_true", default=False, help="Very Verbose mode.")
    
    subparsers = parser.add_subparsers(dest='action', help='choose an action')
 
    parser_h = subparsers.add_parser('hide', description='Description of *hide* subcommand', help='Hide data in image')
    parser_h.add_argument("-n", "--dimension", type=int, default=2, required=True, help="each secret digit in a (2n + 1)-ary notational system is carried by n cover pixels, where n is a system parameter, and, at most, only one pixel is increased or decreased by 1")
    parser_h.add_argument("-in", "--input-image", required=True, help="Input image file")
    input = parser_h.add_mutually_exclusive_group()
    input.add_argument("-it", "--input-data-text", help="Data to be hidden in text mode")
    input.add_argument("-if", "--input-data-file", help="Data to be hidden in file mode")
    parser_h.add_argument("-out", "--output-image", help="Output image file")
    
    parser_e = subparsers.add_parser('extract', description='Description of *extract* subcommand', help='Extract data from image')
    parser_e.add_argument("-n", "--dimension", type=int, default=2, required=True, help="each secret digit in a (2n + 1)-ary notational system is carried by n cover pixels, where n is a system parameter, and, at most, only one pixel is increased or decreased by 1")
    parser_e.add_argument("-l", "--length", type=int, required=True, help="Length of bytes to extract")
    parser_e.add_argument("-in", "--input-image", required=True, help="Input image file")
    parser_e.add_argument("-out", "--output-file", help="Output binary file")

    parser_i = subparsers.add_parser('info', description='Description of *info* subcommand', help='Return info about image capacity')
    parser_i.add_argument("-in", "--input-image", required=True, help="Input image file")

    parser_s = subparsers.add_parser('search', description='Description of *search* subcommand', help='search text hidden into image')
    parser_s.add_argument("-l", "--length", type=int, required=True, help="Length of bytes to extract")
    parser_s.add_argument("-in", "--input-image", required=True, help="Input image file")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    return parser.parse_args()

def header() -> None:
    print(r"""  ______ __  __ _____     _____ _                               
 |  ____|  \/  |  __ \   / ____| |                              
 | |__  | \  / | |  | | | (___ | |_ ___  __ _  __ _ _ __   ___  
 |  __| | |\/| | |  | |  \___ \| __/ _ \/ _` |/ _` | '_ \ / _ \           v2.1
 | |____| |  | | |__| |  ____) | ||  __/ (_| | (_| | | | | (_) |
 |______|_|  |_|_____/  |_____/ \__\___|\__, |\__,_|_| |_|\___/           @totoiste
                                         __/ |                  
                                        |___/                   
  -----Efficient Steganographic Embedding by Exploiting Modification Direction-----
""")

if __name__ == '__main__':
    BYTE_LENGTH = 8
    SUFFIX_OUTPUT_FILE = '_EMD'
 
    header()
    options = parseArgs()

    try:
        match options.action:
            case 'info':
                Img = IMAGE(options.input_image)
                nb_pixels = Img.get_nb_pixels()
                if Img.mode != 'L':
                    print(f"\x1b[1;93m⚠\x1b[0m \x1b[96mImage not in grayscale -> will be converted\x1b[0m")
                print(f"\x1b[1;92m✅\x1b[0m \x1b[96mYou can hide a total of {nb_pixels // BYTE_LENGTH} bytes in {options.input_image}\x1b[0m")

            case 'hide':
                Steg = EMD(options.dimension)
                Img  = IMAGE(options.input_image)
                if Img.mode != 'L':
                    print(f"\x1b[1;93m⚠\x1b[0m \x1b[96mImage has been converted in grayscale\x1b[0m")
                    
                Data = ""
                if options.input_data_text:
                    Data = SECRET(options.input_data_text, options.dimension)
                elif options.input_data_file:
                    with open(options.input_data_file, 'rb') as f:
                        Data = SECRET(f.read(), options.dimension)
                
                Img_steg = Steg.hide(Data, Img)
                
                output_image_path = ""
                if options.output_image:
                    output_image_path = options.output_image
                else:
                    name, extension = os.path.splitext(options.input_image)
                    output_image_path = f"{name}{SUFFIX_OUTPUT_FILE}{extension}"
                Img_steg.save(output_image_path)
                print(f"\x1b[1;92m✅\x1b[0m \x1b[96mMessage hidden in {output_image_path} \x1b[0m")
                
            case 'extract':
                Steg = EMD(options.dimension)
                Img_steg = IMAGE(options.input_image)
                Secret = Steg.extract(Img_steg, options.length)
                
                if options.output_file:
                    with open(options.output_file, "wb") as file:
                        file.write(Secret.bytes)
                    file.close()
                    print(f"\x1b[1;92m✅\x1b[0m \x1b[96mFile {options.output_file} has been saved !\x1b[0m")
                else:
                    print(f"\x1b[1;92m✅\x1b[0m \x1b[96mEMD Data = {Secret.bytes}\x1b[0m")

            case 'search':
                Img_steg = IMAGE(options.input_image)
                n_max = Img_steg.width - 1 #Should be different...
                for n in range(2,n_max):
                    nb_bytes_max = (Img_steg.get_nb_pixels() // BYTE_LENGTH // n)
                    if options.debug or options.verbose:
                        print(f"\x1b[1m[\x1b[93m+\x1b[0m\x1b[1m]\x1b[0m Searching text with {n = }/{n_max}\x1b[0m")
                    Steg = EMD(n)
                    bytes_candidate = Steg.extract(Img_steg, nb_bytes_max)
                    result = bytes_candidate.find_printable_substring(options.length)
                    if result is not None:
                        (bytes_printable, offset, bit_shift) = result
                        print(f"\x1b[1;92m✅\x1b[0m \x1b[96mFound = {bytes_printable} with {n = }, {offset = }, {bit_shift = }\x1b[0m")

            case _:
                parser.print_help()
    except Exception as e:
        print(f"\x1b[1;91m❌\x1b[0m \x1b[96m{type(e)} : {e}\x1b[0m")
