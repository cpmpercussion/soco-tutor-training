#!/usr/bin/env python3
"""Generate the pandoc pptx reference doc (templates/reference.pptx).

Starts from pandoc's built-in reference.pptx and rewrites it:

- Enlarges the canvas from pandoc's small 10in x 5.63in 16:9 to standard
  13.33in x 7.5in, scaling every master/layout placeholder to match.
  (The small canvas with full-size fonts is why text overflows.)
- Sets sensible text sizes: 32pt bold left-aligned titles, 20pt body,
  matching the text density of the reveal.js slides at 1920x1080.
- Applies the charles_reveal_dark colour scheme (see css/).

Usage: python3 templates/make_reference_pptx.py templates/reference.pptx
"""

import io
import re
import subprocess
import sys
import zipfile

SCALE = 4 / 3  # 9144000x5143500 EMU -> 12192000x6858000 EMU (13.33in x 7.5in)

# Aptos is the Microsoft 365 default font (successor to Calibri), so it
# renders identically for anyone opening these decks in current Office.
FONT = "Aptos"

# Colours from css/charles_reveal_dark.scss
THEME_COLOURS = {
    "dk1": "FAFAFA",      # text  ($text-color)
    "lt1": "15272E",      # background ($darker-charcoal)
    "dk2": "D5DDE0",      # secondary text
    "lt2": "264653",      # secondary background ($charcoal)
    "accent1": "2A9D8F",  # $persian-green
    "accent2": "E76F51",  # $burnt-sienna
    "accent3": "E9C46A",  # $saffron
    "accent4": "F4A261",  # $sandy-brown
    "accent5": "7FB3BF",
    "accent6": "9B59B6",
    "hlink": "E76F51",    # $link-color
    "folHlink": "F4A261",
}

# master body text sizes, default -> ours (in 1/100 pt)
BODY_SIZES = {"2400": "2000", "2100": "1800", "1800": "1600", "1500": "1400"}


def scale_coords(xml: str) -> str:
    """Scale all x/y/cx/cy EMU coordinates by SCALE."""
    return re.sub(
        r'\b(x|y|cx|cy)="(\d+)"',
        lambda m: f'{m.group(1)}="{round(int(m.group(2)) * SCALE)}"',
        xml,
    )


def fix_layout(xml: str) -> str:
    """Scale a slide layout and drop its hard-coded font sizes.

    Several layouts (Two Content, Comparison, Content with Caption, ...)
    override the master text styles with explicit sizes as small as 7pt
    and suppress bullets; pandoc puts ordinary body text in those
    placeholders, so strip the overrides and let everything inherit the
    master styles instead. (Pandoc emits its own buNone for non-list
    paragraphs, so list bullets stay correct.)
    """
    xml = scale_coords(xml)
    xml = re.sub(r' sz="\d+"', "", xml)
    xml = re.sub(r' (?:marL|indent)="-?\d+"', "", xml)
    return xml.replace("<a:buNone/>", "")


def fix_presentation(xml: str) -> str:
    return re.sub(
        r"<p:sldSz[^/]*/>", '<p:sldSz cx="12192000" cy="6858000"/>', xml
    )


def fix_theme(xml: str) -> str:
    for name, hexval in THEME_COLOURS.items():
        xml = re.sub(
            rf"<a:{name}>.*?</a:{name}>",
            f'<a:{name}><a:srgbClr val="{hexval}"/></a:{name}>',
            xml,
        )
    # heading (major) and body (minor) fonts
    xml = xml.replace(
        '<a:latin typeface="Calibri"/>', f'<a:latin typeface="{FONT}"/>'
    )
    return xml


def fix_master(xml: str) -> str:
    xml = scale_coords(xml)

    # Titles: 33pt centred -> 32pt bold left-aligned (like reveal headings)
    def edit_title(m: re.Match) -> str:
        s = m.group(0)
        s = s.replace('algn="ctr"', 'algn="l"')
        s = s.replace('sz="3300" kern="1200"', 'sz="3200" b="1" kern="1200"')
        return s

    xml = re.sub(r"<p:titleStyle>.*?</p:titleStyle>", edit_title, xml, flags=re.S)

    # Body: shrink each indent level, colour the bullets persian-green
    def edit_body(m: re.Match) -> str:
        s = m.group(0)
        for old, new in BODY_SIZES.items():
            s = s.replace(f'sz="{old}"', f'sz="{new}"')
        s = s.replace(
            "</a:spcBef><a:buFont",
            '</a:spcBef><a:buClr><a:schemeClr val="accent1"/></a:buClr><a:buFont',
        )
        return s

    xml = re.sub(r"<p:bodyStyle>.*?</p:bodyStyle>", edit_body, xml, flags=re.S)
    return xml


def main(out_path: str) -> None:
    default = subprocess.run(
        ["pandoc", "--print-default-data-file", "reference.pptx"],
        capture_output=True,
        check=True,
    ).stdout

    src = zipfile.ZipFile(io.BytesIO(default))
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "ppt/presentation.xml":
                data = fix_presentation(data.decode("utf-8")).encode("utf-8")
            elif item.filename == "ppt/theme/theme1.xml":
                data = fix_theme(data.decode("utf-8")).encode("utf-8")
            elif item.filename == "ppt/slideMasters/slideMaster1.xml":
                data = fix_master(data.decode("utf-8")).encode("utf-8")
            elif item.filename.startswith("ppt/slideLayouts/slideLayout"):
                data = fix_layout(data.decode("utf-8")).encode("utf-8")
            dst.writestr(item, data)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "templates/reference.pptx")
