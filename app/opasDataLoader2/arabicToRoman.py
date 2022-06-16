

import re
import six
from six.moves import range

iv = re.compile("IV")
ix = re.compile("IX")
xl = re.compile("XL")
xc = re.compile("XC")
cd = re.compile("CD")
cm = re.compile("CM")
i = re.compile("I" )
v = re.compile("V" )
x = re.compile("X" )
l = re.compile("L" )
c = re.compile("C" )
d = re.compile("D" )
m = re.compile("M" )

def romanNumeralsToDecimal(roman_string):
    the_str = roman_string.upper()

    if iv.search(the_str) != None:  the_str = iv.sub("+4",    the_str)
    if ix.search(the_str) != None:  the_str = ix.sub("+9",    the_str)
    if xl.search(the_str) != None:  the_str = xl.sub("+40",   the_str)
    if xc.search(the_str) != None:  the_str = xc.sub("+90",   the_str)
    if cd.search(the_str) != None:  the_str = cd.sub("+400",  the_str)
    if cm.search(the_str) != None:  the_str = cm.sub("+900",  the_str)
    if  i.search(the_str) != None:  the_str =  i.sub("+1",    the_str)
    if  v.search(the_str) != None:  the_str =  v.sub("+5",    the_str)
    if  x.search(the_str) != None:  the_str =  x.sub("+10",   the_str)
    if  l.search(the_str) != None:  the_str =  l.sub("+50",   the_str)
    if  c.search(the_str) != None:  the_str =  c.sub("+100",  the_str)
    if  d.search(the_str) != None:  the_str =  d.sub("+500",  the_str)
    if  m.search(the_str) != None:  the_str =  m.sub("+1000", the_str)
    exec("num = " + the_str)
    return num
    
def arabic_to_roman(base10_integer):
    """additional function name - pep PEPNew Naming Convention"""
    
def decimalToRomanNumerals(base10_integer):
    """
    Convert arabic numbers to roman
    
    Translated from a public domain C routine by Jim Walsh in the
    Snippets collection.
    
    >>> print(decimalToRomanNumerals(5000))
    MMMMM
    >>> print(decimalToRomanNumerals(6000))
    MMMMMM
    >>> print(decimalToRomanNumerals(9000))
    MMMMMMMMM
    >>> print(decimalToRomanNumerals(6999))    
    MMMMMMCMXCIX
    """
    roman = ""
    n, base10_integer = divmod(base10_integer, 1000)
    roman = "M"*n
    if base10_integer >= 900:
        roman = roman + "CM"
        base10_integer = base10_integer - 900
    while base10_integer >= 500:
        roman = roman + "D"
        base10_integer = base10_integer - 500
    if base10_integer >= 400:
        roman = roman + "CD"
        base10_integer = base10_integer - 400
    while base10_integer >= 100:
        roman = roman + "C"
        base10_integer = base10_integer - 100
    if base10_integer >= 90:
        roman = roman + "XC"
        base10_integer = base10_integer - 90
    while base10_integer >= 50:
        roman = roman + "L"
        base10_integer = base10_integer - 50
    if base10_integer >= 40:
        roman = roman + "XL"
        base10_integer = base10_integer - 40
    while base10_integer >= 10:
        roman = roman + "X"
        base10_integer = base10_integer - 10
    if base10_integer >= 9:
        roman = roman + "IX"
        base10_integer = base10_integer - 9
    while base10_integer >= 5:
        roman = roman + "V"
        base10_integer = base10_integer - 5
    if base10_integer >= 4:
        roman = roman + "IV"
        base10_integer = base10_integer - 4
    while base10_integer > 0:
        roman = roman + "I"
        base10_integer = base10_integer - 1
    return roman

if __name__ == "__main__":
    '''We'll test the conversion routines by converting from a decimal
    integer n to a Roman numeral and then back again.  If the operations
    are not the identity transformation, it's an error.
    '''
    largest_number = 9000
    for num in range(1,largest_number+1):
        str = decimalToRomanNumerals(int(num))
        number = romanNumeralsToDecimal(str)
        if number != num:
            print("Routines failed for", num)
            raise "Test failure"

    import doctest
    print("Range Test passed.")
    print("Doctests starting...")
    doctest.testmod()
    print("Finished!")
