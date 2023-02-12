#!/usr/sbin/python3
# v1.0

from colour import Color
import re  # for sed
import os  # for mkdir


def complementary(primary_color, n):
    n += 1
    clist = []
    hue = primary_color.hue
    s = primary_color.saturation
    l = primary_color.luminance
    for f in map(lambda x: x/n, range(0, n, 1)):  # f: [0 -> x[, step = 1/n
        if(f % 1.0 == 0.0):
            continue
        new_hue = (hue + f) % 1.0
        new_color = Color(hue=new_hue, saturation=s, luminance=l)
        clist.append(new_color)
    return clist


# r = 1/5
#   range: 1/5 means we go to hues that deviate at most of 1/5th from primary color
#   (in a 360° hue, that's 72°)
# for f in map...
#   - if even, f: [-(n-1)r/n -> (n+1)r/n[, step=2(r/n)
#     n = 6: ~-0.17 -> ~0.23, step~=0.07 (-0.17, -0.1, -0.03, 0.03, 0.1, 0.17)
#   - if odd,  f: [-r -> r[, step=2(r/n)
#     n = 5: -0.2 -> 0.2, step~=0.07 (-0.2, -0.13, -0.07, 0 (not counted), 0.07, 0.13)
def analogous(primary_color, n):
    start, step = (0, 0)
    if(n % 2 == 0):
        start = -n+1
        stop = n+1
    else:
        start = -n
        stop = n
    clist = []
    hue = primary_color.hue
    s = primary_color.saturation
    l = primary_color.luminance

    r = 1/5

    for f in map(lambda x: x * r / n, range(start, stop, 2)):
        if(f % 1.0 == 0.0):
            continue
        new_hue = (hue + f) % 1.0
        new_color = Color(hue=new_hue, saturation=s, luminance=l)
        clist.append(new_color)
    return clist


# lumList = for instance (1.0, 2/3, 1/3, 0.1) to get normal, dark, darker, darkest shades
# (that was the values I used at first but I changed it)
def shades(primary_color, lumList):
    clist = []
    h = primary_color.hue
    s = primary_color.saturation
    lum = primary_color.luminance
    for l in lumList:
        new_color = Color(hue=h, saturation=s, luminance=(lum * l))
        clist.append(new_color)
    return clist


def debug(primary_color, n, mode):
    print("Debug mode (entered with mode: " + mode + ")")
    print("Primary color:", primary_color.hex_l)
    print("Complementary colors:", complementary(primary_color, n))
    print("Analogous colors:", analogous(primary_color, n))
    # old shade values
    print("Shades:", shades(primary_color, (1.0, 2/3, 1/3, 0.05)))
    exit()


def use_mode(primary_color, n, mode):
    if(mode == "Analogous"):
        return analogous(primary_color, n)
    elif(mode == "Complementary"):
        return complementary(primary_color, n)
    elif(mode == "Debug"):
        return debug(primary_color, n, mode)
    else:
        print("Modes: Analogous, Complementary, Debug")
        return debug(primary_color, n, f"{mode}")


# give it a light color
# returns:
#   - n dark colors
#   - n bright colors
#   - 4 monochrome shades
def color_to_scheme(primary_color_string, n, mode="Debug"):
    primary_color = Color(primary_color_string)
    lumAbsList = (0.99, primary_color.luminance, 1/6, 0.01)
    lumList = []
    for l in lumAbsList:
        h = primary_color.hue
        lumList.append(l/h)
    bright_colors = use_mode(primary_color, n, mode)
    if(mode == "Debug"):
        return
    dark_colors = []
    for c in bright_colors:
        nc = Color(hue=c.hue, saturation=c.saturation,
                   luminance=lumAbsList[2]/c.luminance)
        dark_colors.append(nc)
    for b in bright_colors:
        b.luminance *= 2/3
    greys = shades(primary_color, lumList)
    colors = {
        'd': dark_colors,
        'b': bright_colors,
        'g': greys,
    }
    return colors


def terminal_scheme(primary_color_string, mode="Complementary", name=""):
    if(name == ""):  # if no name given, name derived from color and mode
        name = f"{primary_color_string.lower()}-{mode.lower()}"
    colors_dict = color_to_scheme(primary_color_string, 6, mode)
    color_scheme = {
        # black
        0: colors_dict['g'][3].hex_l,
        8: colors_dict['g'][2].hex_l,

        # red
        1: colors_dict['d'][0].hex_l,
        9: colors_dict['b'][0].hex_l,

        # green
        2: colors_dict['d'][1].hex_l,
        10: colors_dict['b'][1].hex_l,

        # yellow
        3: colors_dict['d'][2].hex_l,
        11: colors_dict['b'][2].hex_l,

        # blue
        4: colors_dict['d'][3].hex_l,
        12: colors_dict['b'][3].hex_l,

        # magenta
        5: colors_dict['d'][4].hex_l,
        13: colors_dict['b'][4].hex_l,

        # cyan
        6: colors_dict['d'][5].hex_l,
        14: colors_dict['b'][5].hex_l,

        # white
        7: colors_dict['g'][1].hex_l,
        15: colors_dict['g'][0].hex_l,
    }

    # feel free to comment either of those if you don't need it
    # (or both but then you won't get any file)
    Xresources = scheme_to_Xresources(color_scheme)
    linux_console = scheme_to_linux_console(color_scheme)
    filename = f"output/{name}"  # .ext
    write_to_file(Xresources, filename + ".colors.Xresources")
    write_to_file(linux_console, filename + ".sh")

    return color_scheme


def scheme_to_Xresources(color_scheme, comment=""):
    Xresources = ""
    if(comment != ""):
        comment = re.sub(r"^", r"! ", comment, re.M)
        comment = re.sub(r"\n", r"\n! ", comment, re.M)
        Xresources += comment
    Xresources += f"""\n
! special
*.foreground: {color_scheme[7]}
*.background: {color_scheme[0]}
*.cursorColor: {color_scheme[7]}
"""

    colors = ("black", "red", "green", "yellow",
              "blue", "magenta", "cyan", "white")

    for i in range(0, 8):
        Xresources += f"""
! {colors[i]}
*.color{i}: {color_scheme[i]}
*.color{i+8}: {color_scheme[i+8]}
"""
    return Xresources


def scheme_to_linux_console(color_scheme, comment=""):
    shell_script = "#!/bin/sh"
    if(comment != ""):
        comment = re.sub(r"^", r"# ", comment, re.M)
        comment = re.sub(r"\n", r"\n# ", comment, re.M)
        shell_script += "\n" + comment
    shell_script += """
if [ "$TERM" = "linux" ]; then
  /bin/echo -e \""""
    for i in range(0, 16):
        shell_script += f"\n  \e]P{hex(i)[2:].upper()}{color_scheme[i][1:]}"
    shell_script += """
  "
  # get rid of artifacts
  clear
fi"""
    return shell_script


def write_to_file(string, filename):
    folder = re.sub(r"(.*)/.*", r"\1", filename, re.M)
    if not os.path.exists(folder):
        os.makedirs(folder)
    f = open(filename, "w")
    f.write(string)
    f.close


pink_scheme_complementary = terminal_scheme("Pink", "Complementary")
pink_scheme_analogous = terminal_scheme(
    "Pink", "Analogous", name="pink-analogous")
