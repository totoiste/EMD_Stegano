#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : EMD_Stegano.py
# Author             : totoiste (@T0to1st3)
# Date created       : 13/07/2025

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
    - digit_index is the index in digits which are the conversion of DATA to be hidden in numbers
        As a digit is coded in n pixels, the n-th digit position could be calculated -> get_coord_xy()
    - stego_group is a group of n pixels hiding one bit of DATA

"""
class IMAGE:
    def __init__(self, image_path) -> None:
        try:
            img = Image.open(image_path)
        except Exception:
            print(f"\x1b[1;91m❌\x1b[0m \x1b[96mNot an image file !\x1b[0m")
        self.img = img
        self.mode = img.mode
        self.pixels = img.load()
        self.width, self.height = img.size

    def convert_grayscale(self) -> None:
        self.img = self.img.convert("L")
        
    def get_nb_pixels(self) -> int:
        return self.width*self.height

    def save(self, image_output_path) -> None:
        self.img.save(image_output_path)

    def get_coord_xy(self, digit_index, n) -> list:
        digits_by_line = self.width // n
        y = digit_index // digits_by_line 
        x = (digit_index % digits_by_line) * n
        return x, y

    def get_stego_group(self, digit_index, n) -> list:
        x, y = self.get_coord_xy(digit_index, n)
        p = [self.pixels[x + i, y] for i in range(n)]
        if options.verbose:
            print(f"\x1b[1m[\x1b[93m++\x1b[0m\x1b[1m]\x1b[0m get_stego_group of {digit_index = } : {x = }, {y = }, {p = }\x1b[0m")
        return p

    def set_stego_group(self, stego_group, digit_index, n):
        x, y = self.get_coord_xy(digit_index, n)
        for i in range(n):
            self.pixels[x + i, y] = stego_group[i]
        #print(f"set_stego_group of {digit_index = } : {x = }, {y = }, {stego_group = }")
        #return self

"""
Class DATA
-----------
    - This class is usefull to manage DATA to hide in IMAGE or to manage SECRET
      extracted from IMAGE
    - data can be a string, byte or array of bits
"""
class DATA:
    def __init__(self, data) -> None:
        self.length = len(data)

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

        self.bits = self.bytes_to_bits(self.bytes)

    def bytes_to_bits(self, byte_values) -> list:
        bit_list = []
        for char in byte_values:
            bit_list.extend([int(b) for b in bin(char)[2:].zfill(BYTE_LENGTH)])
        return bit_list

    def bits_to_bytes(self, bit_list) -> bytes:
        num_bytes = len(bit_list) // BYTE_LENGTH
        byte_values = []
        for i in range(num_bytes):
            byte_bits = bit_list[i*BYTE_LENGTH : (i+1)*BYTE_LENGTH]
            binary_string = "".join(str(b) for b in byte_bits)
            decimal_value = int(binary_string, 2)
            byte_values.append(decimal_value)
        return bytes(byte_values)

    def find_printable_substring(self, length, tolerance = 0.90) -> list: 
        for b in range(BYTE_LENGTH):
            raw_bytes = self.bits_to_bytes(self.bits[b:])
            for i in range(len(raw_bytes) - length + 1):
                substring_bytes = raw_bytes[i:i + length]
                decoded_substring = substring_bytes.decode('utf-8', errors='ignore')
                printable_count = sum(1 for char in decoded_substring if char.isprintable())
                #print(f"{len(self.bytes) = } {i = } {decoded_substring = } and {printable_count = }")
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
    def __init__(self, n) -> None:
        self.n = n
        self.base = 2 * n + 1
        self.bits_per_digit = math.floor(math.log2(self.base))
        if options.debug:
            print(f"\x1b[1m[\x1b[93m+\x1b[0m\x1b[1m]\x1b[0m n = {self.n}, base (2n+1) = {self.base}, bits per digit = {self.bits_per_digit}\x1b[0m")

    # Calulation of f as a weighted sum modulo (2n + 1) 
    # f(g1, g2,...,gn) = SUM[(gi*i)] mod (2n + 1) for i = 1..n
    def f(self, pixel_values) -> int:
        weighted_sum = 0
        for i in range(self.n):
            weighted_sum += (i + 1) * pixel_values[i]
        return weighted_sum % self.base

    #Convert digits in a (2n + 1)-ary notational system to bits
    def convert_digits2bits(self, digits, data_length) -> list:
        bits = []
        for digit in digits:
            binary = bin(digit)[2:].zfill(int(self.bits_per_digit))
            bits.extend([int(b) for b in binary])
        #Keep the exact quantity of bits...
        bits = bits[:data_length * BYTE_LENGTH]
        if options.debug:
            print(f"\x1b[1m[\x1b[93m+\x1b[0m\x1b[1m]\x1b[0m Convert {len(bits)} bits from {len(digits)} digits\x1b[0m")
        return bits

    #Modify the correct pixel by incrementing or decrementing of 1 
    #Manage the cases of pixel values = 0 or 255
    def embed(self, data_digit, stego_group) -> list:
        current_digit = self.f(stego_group)

        if current_digit != data_digit:
            s = (data_digit - current_digit) % self.base
            if s <= self.n:
                pos = s - 1
                pixel_to_change = stego_group[pos]
                if pixel_to_change == 255:
                    #print(f"{pixel_to_change = } {stego_group = } {self.base = } {s = } {pos = } {stego_group[pos] = }")
                    stego_group[pos] -= 1
                    stego_group = self.embed(data_digit, stego_group)
                else:
                    stego_group[pos] = pixel_to_change + 1
            elif s > self.n:
                pos = self.base - s - 1
                pixel_to_change = stego_group[pos]
                if pixel_to_change == 0:
                    #print(f"{pixel_to_change = } {stego_group = } {self.base = } {s = } {pos = }")
                    stego_group[pos] += 1
                    stego_group = self.embed(data_digit, stego_group)
                else:
                    stego_group[pos] = pixel_to_change - 1
        return stego_group

    def hide_digit(self, data_digit, Img, digit_index) -> None:
        p = Img.get_stego_group(digit_index,self.n)
        p = self.embed(data_digit, p)
        Img.set_stego_group(p, digit_index, self.n)

    # Hide each byte of data in image
    def hide(self, Data, Img):
        if options.debug:
            print(f"\x1b[1m[\x1b[93m+\x1b[0m\x1b[1m]\x1b[0m Data to hide : {len(Data.bytes)} bytes and {len(Data.bits)} bits\x1b[0m")
        required_digits = math.ceil(len(Data.bits) / self.bits_per_digit)
        if options.debug:
            print(f"\x1b[1m[\x1b[93m+\x1b[0m\x1b[1m]\x1b[0m Required digits (stego_group) to hide Data : {required_digits}\x1b[0m")

        if Img.width * Img.height < required_digits * self.n:
            raise ValueError(f"\x1b[1;91m❌\x1b[0mImage too small : {Img.width * Img.height} pixels available, {required_digits * n} required !\x1b[0m")

        #print(f"Last byte of data = {Data.bits[-24:]}")
        digits = self.set_digits(Data.bits)
        #print(f"Last 30 numbers {self.base}-ary to hide :", digits[-30:])

        digit_index = 0
        while digit_index < len(digits) :
            data_digit = digits[digit_index]
            self.hide_digit(data_digit, Img, digit_index)
            digit_index += 1

        print(f"\x1b[1;92m✅\x1b[0m \x1b[96mData of {Data.length} bytes hidden with {digit_index} digits of base {self.base} and {len(Data.bits)} bits\x1b[0m")
        return Img

    # Extract and calculate digits from IMAGE 
    def get_digits(self, Img, data_length) -> list:
        digits = []
        digit_index = 0
        while len(digits) * self.bits_per_digit < data_length * BYTE_LENGTH :
            p = Img.get_stego_group(digit_index, self.n)
            digits.append(self.f(p))
            digit_index += 1
        if options.debug:
            print(f"\x1b[1m[\x1b[93m+\x1b[0m\x1b[1m]\x1b[0m Get {len(digits)} digits from image\x1b[0m")
        return digits

    #Convert bits to digits in a (2n + 1)-ary notational system
    def set_digits(self, bits) -> list:
        # Add padding With '0' if needed
        remainder = len(bits) % self.bits_per_digit
        if remainder != 0:
            bits = bits + [0] * (self.bits_per_digit - remainder)

        digits = []
        for i in range(0, len(bits), self.bits_per_digit):
            group = bits[i : i + self.bits_per_digit]
            number = int(''.join(map(str, group)),2)
            digits.append(number)
        if options.debug:
            print(f"\x1b[1m[\x1b[93m+\x1b[0m\x1b[1m]\x1b[0m Convert {len(digits)} digits from {len(bits)} bits\x1b[0m")
        return digits

    def extract(self, Img, data_length) -> bytes:
        digits = self.get_digits(Img, data_length)

        bits = self.convert_digits2bits(digits, data_length)
        if options.verbose:
            print(f"\x1b[1m[\x1b[93m++\x1b[0m\x1b[1m]\x1b[0m numbers {self.base}-ary extracted : {digits}\x1b[0m")
            print(f"\x1b[1m[\x1b[93m++\x1b[0m\x1b[1m]\x1b[0m Extracted Message in {len(bits)} bits\x1b[0m")
            print(f"\x1b[1m[\x1b[93m++\x1b[0m\x1b[1m]\x1b[0m bits of Secret = {bits}\x1b[0m")
        Secret = DATA(bits)
        if options.debug:
            print(f"\x1b[1m[\x1b[93m+\x1b[0m\x1b[1m]\x1b[0m Extracted {Secret.length // BYTE_LENGTH} bytes from image\x1b[0m")
        return Secret

def parseArgs() -> dict:
    parser = argparse.ArgumentParser(add_help=True, description="The EMD_Stegano script allows you to hide DATA in an image or read hidden DATA from an image with a Steganographic process called EMD (Exploiting Modification Direction)")
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
 |  __| | |\/| | |  | |  \___ \| __/ _ \/ _` |/ _` | '_ \ / _ \           v1.1
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
                print(f"\x1b[1;92m✅\x1b[0m \x1b[96mYou can hide a total of {nb_pixels // BYTE_LENGTH} // n bytes with n > 2 in {options.input_image}\x1b[0m")

            case 'hide':
                Steg = EMD(options.dimension)
                Img  = IMAGE(options.input_image)
                if Img.mode != 'L':
                    print(f"\x1b[1;93m⚠\x1b[0m \x1b[96mImage has been converted in grayscale\x1b[0m")
                    
                Data = ""
                if options.input_data_text:
                    Data = DATA(options.input_data_text)
                elif options.input_data_file:
                    Data = DATA(options.input_data_file)
                
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
                #n_max = Img_steg.width - 1 #Should be different...
                n_max = 20
                for n in range(2,n_max):
                    nb_bytes_max = (Img_steg.get_nb_pixels() // BYTE_LENGTH // n)
                    if options.debug:
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
